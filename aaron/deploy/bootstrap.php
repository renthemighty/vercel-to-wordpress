<?php
/* one-shot installer, token gated. delete after use. */
@set_time_limit(0);
@ini_set('memory_limit','512M');
header('Content-Type: text/plain; charset=utf-8');
header('Cache-Control: no-store, no-cache, must-revalidate');
$TOKEN = '__TOKEN__';
if (!isset($_GET['k']) || !hash_equals($TOKEN, (string)$_GET['k'])) { http_response_code(404); echo "nope\n"; exit; }
$root = __DIR__;
$step = isset($_GET['step']) ? $_GET['step'] : 'info';
function out($k, $v) { echo str_pad($k, 24) . ' ' . $v . "\n"; }
function fetch_to($url, $dest) {
    $fp = fopen($dest, 'wb');
    if (!$fp) return 'cannot open ' . $dest;
    $ch = curl_init($url);
    curl_setopt_array($ch, [CURLOPT_FILE => $fp, CURLOPT_FOLLOWLOCATION => true, CURLOPT_TIMEOUT => 300, CURLOPT_USERAGENT => 'Mozilla/5.0']);
    $ok = curl_exec($ch);
    $code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    $err = curl_error($ch);
    curl_close($ch); fclose($fp);
    if (!$ok || $code >= 400) return "http $code $err";
    return true;
}
function unzip_to($zip, $dir) {
    $z = new ZipArchive();
    if ($z->open($zip) !== true) return 'cannot open zip';
    $z->extractTo($dir); $z->close(); return true;
}
function rmove($src, $dst) {
    $d = opendir($src);
    while (($f = readdir($d)) !== false) {
        if ($f === '.' || $f === '..') continue;
        $s = "$src/$f"; $t = "$dst/$f";
        if (is_dir($s)) { if (!is_dir($t)) mkdir($t, 0755, true); rmove($s, $t); rmdir($s); }
        else { if (file_exists($t)) unlink($t); rename($s, $t); }
    }
    closedir($d);
}

if ($step === 'info') {
    out('php', PHP_VERSION);
    out('root', $root);
    out('writable', is_writable($root) ? 'yes' : 'NO');
    out('curl', function_exists('curl_init') ? 'yes' : 'NO');
    out('zip', class_exists('ZipArchive') ? 'yes' : 'NO');
    out('mysqli', function_exists('mysqli_connect') ? 'yes' : 'NO');
    out('memory_limit', ini_get('memory_limit'));
    out('max_execution_time', ini_get('max_execution_time'));
    out('wp_present', file_exists("$root/wp-load.php") ? 'yes' : 'no');
    out('files', implode(', ', array_slice(array_diff(scandir($root), ['.', '..']), 0, 20)));
    exit;
}

if ($step === 'fetch') {
    $tmp = "$root/.boot"; if (!is_dir($tmp)) mkdir($tmp, 0755, true);
    $r = fetch_to('https://wordpress.org/latest.zip', "$tmp/wp.zip");
    out('wp download', $r === true ? filesize("$tmp/wp.zip") . ' bytes' : $r);
    if ($r !== true) exit;
    $r = unzip_to("$tmp/wp.zip", $tmp);
    out('wp unzip', $r === true ? 'ok' : $r);
    if (!is_dir("$tmp/wordpress")) { out('wp dir', 'MISSING'); exit; }
    rmove("$tmp/wordpress", $root); rmdir("$tmp/wordpress");
    out('wp moved', file_exists("$root/wp-load.php") ? 'yes' : 'NO');
    $r = fetch_to('https://downloads.wordpress.org/plugin/woocommerce.zip', "$tmp/woo.zip");
    out('woo download', $r === true ? filesize("$tmp/woo.zip") . ' bytes' : $r);
    if ($r === true) {
        $r = unzip_to("$tmp/woo.zip", "$root/wp-content/plugins");
        out('woo unzip', $r === true ? 'ok' : $r);
        out('woo present', file_exists("$root/wp-content/plugins/woocommerce/woocommerce.php") ? 'yes' : 'NO');
    }
    @unlink("$tmp/wp.zip"); @unlink("$tmp/woo.zip");
    exit;
}

if ($step === 'config') {
    $db = $_GET['db']; $du = $_GET['du']; $dp = $_GET['dp'];
    $sample = file_get_contents("$root/wp-config-sample.php");
    if (!$sample) { out('config', 'no wp-config-sample.php'); exit; }
    $c = $sample;
    $c = str_replace("database_name_here", $db, $c);
    $c = str_replace("username_here", $du, $c);
    $c = str_replace("password_here", $dp, $c);
    $salts = @file_get_contents('https://api.wordpress.org/secret-key/1.1/salt/');
    if ($salts && strpos($salts, 'AUTH_KEY') !== false) {
        $c = preg_replace("/define\(\s*'(AUTH_KEY|SECURE_AUTH_KEY|LOGGED_IN_KEY|NONCE_KEY|AUTH_SALT|SECURE_AUTH_SALT|LOGGED_IN_SALT|NONCE_SALT)'.*?\);\r?\n/s", '', $c, 8);
        $c = str_replace("/**#@-*/", $salts . "\n/**#@-*/", $c);
    }
    $extra = "\ndefine('FS_METHOD','direct');\ndefine('WP_AUTO_UPDATE_CORE','minor');\ndefine('DISALLOW_FILE_EDIT',true);\n";
    $c = str_replace("/* That's all, stop editing!", $extra . "\n/* That's all, stop editing!", $c);
    file_put_contents("$root/wp-config.php", $c);
    out('wp-config', file_exists("$root/wp-config.php") ? strlen($c) . ' bytes' : 'FAILED');
    $link = @mysqli_connect('localhost', $du, $dp, $db);
    out('db connect', $link ? 'ok' : mysqli_connect_error());
    exit;
}

if ($step === 'install') {
    $url = $_GET['url']; $title = $_GET['title']; $adminuser = $_GET['au']; $adminpass = $_GET['ap']; $adminmail = $_GET['am'];
    define('WP_INSTALLING', true);
    require_once "$root/wp-load.php";
    require_once ABSPATH . 'wp-admin/includes/upgrade.php';
    require_once ABSPATH . 'wp-includes/class-wpdb.php';
    if (is_blog_installed()) { out('install', 'already installed'); exit; }
    $res = wp_install($title, $adminuser, $adminmail, true, '', $adminpass);
    out('install', is_wp_error($res) ? $res->get_error_message() : 'user ' . $res['user_id']);
    update_option('siteurl', $url); update_option('home', $url);
    out('siteurl', get_option('siteurl'));
    exit;
}

if ($step === 'cleanup') {
    @unlink("$root/.boot/wp.zip"); @unlink("$root/.boot/woo.zip"); @rmdir("$root/.boot");
    out('self', 'deleting');
    @unlink(__FILE__);
    out('gone', file_exists(__FILE__) ? 'STILL THERE' : 'yes');
    exit;
}
out('step', 'unknown');

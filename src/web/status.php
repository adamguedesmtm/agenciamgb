<?php
/**
 * CS2 Server Status API
 * Author: adamguedesmtm
 * Created: 2025-02-21 03:19:37
 */

header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');

// Carregar configurações
$config = parse_ini_file('/opt/cs2server/config/.env');

function getServerStatus() {
    global $config;
    $server = @stream_socket_client("udp://{$config['SERVER_IP']}:{$config['SERVER_PORT']}", $errno, $errstr);
    
    if (!$server) {
        error_log("Erro ao conectar ao servidor: $errstr ($errno)");
        return false;
    }
    
    $ping = chr(0xFF).chr(0xFF).chr(0xFF).chr(0xFF)."TSource Engine Query\0";
    fwrite($server, $ping);
    $response = fread($server, 4096);
    fclose($server);
    
    return !empty($response);
}

function getSystemStats() {
    $cpu = shell_exec("top -bn1 | grep 'Cpu(s)' | awk '{print $2}'");
    $memory = shell_exec("free -m | awk 'NR==2{printf \"%.2f%%\", $3*100/$2}'");
    $disk = shell_exec("df -h / | awk 'NR==2{print $5}'");
    $temp = shell_exec("cat /sys/class/thermal/thermal_zone0/temp | awk '{printf \"%.1f°C\", $1/1000}'");

    return [
        'cpu' => trim($cpu) . '%',
        'memory' => trim($memory),
        'disk' => trim($disk),
        'temp' => trim($temp)
    ];
}

function getServicesStatus() {
    return [
        'cs2' => shell_exec("systemctl is-active cs2server") === "active\n",
        'matchzy' => shell_exec("systemctl is-active matchzy") === "active\n",
        'bot' => shell_exec("systemctl is-active cs2bot") === "active\n"
    ];
}

// Gerar resposta
$status = [
    'server' => [
        'online' => getServerStatus(),
        'ip' => $config['SERVER_IP'] . ':' . $config['SERVER_PORT'],
        'last_update' => date('Y-m-d H:i:s')
    ],
    'services' => getServicesStatus(),
    'system' => getSystemStats()
];

echo json_encode($status);
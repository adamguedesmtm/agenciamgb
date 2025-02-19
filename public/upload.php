<?php
// public/upload.php
// Endpoint para upload de demos

include '../config/db.php';

$uploadDir = '/var/www/agenciamgb/storage/uploads/';
$logFile = '/var/www/agenciamgb/storage/logs/upload.log';

if (!is_dir($uploadDir)) {
    mkdir($uploadDir, 0777, true);
}
if (!is_dir('/var/www/agenciamgb/storage/logs')) {
    mkdir('/var/www/agenciamgb/storage/logs', 0777, true);
}

function log_message($message, $logFile = '/var/www/agenciamgb/storage/logs/upload.log') {
    $timestamp = date('Y-m-d H:i:s');
    file_put_contents($logFile, "[$timestamp] $message\n", FILE_APPEND);
}

if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_FILES['demo'])) {
    $demoFile = $uploadDir . basename($_FILES['demo']['name']);
    if (move_uploaded_file($_FILES['demo']['tmp_name'], $demoFile)) {
        // Salva o caminho do arquivo no banco de dados para processamento posterior
        $query = "INSERT INTO demos (file_path, status) VALUES (:file_path, 'pending')";
        $stmt = $conn->prepare($query);
        $stmt->bindParam(':file_path', $demoFile);
        $stmt->execute();

        log_message("Demo enviada com sucesso: {$demoFile}");
        echo json_encode(["mensagem" => "Demo enviada com sucesso. Aguarde o processamento.", "arquivo" => $demoFile]);
    } else {
        log_message("Falha ao enviar demo: {$_FILES['demo']['name']}");
        http_response_code(500);
        echo json_encode(["erro" => "Falha ao enviar demo."]);
    }
}
?>
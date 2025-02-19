<?php
include_once __DIR__ . '/../config/db.php';

$query = "SELECT * FROM demos WHERE status = 'pending' LIMIT 1";
$stmt = $conn->prepare($query);
$stmt->execute();
$demo = $stmt->fetch(PDO::FETCH_ASSOC);

if ($demo) {
    $filePath = $demo['file_path'];
    $outputFile = str_replace('.dem', '.json', $filePath);

    // Processa o arquivo usando CS Demo Manager
    $command = "/caminho/para/cs-demo-manager --input {$filePath} --output {$outputFile}";
    exec($command, $output, $returnVar);

    if ($returnVar === 0) {
        // Lê o JSON gerado e salva no banco de dados
        $jsonData = file_get_contents($outputFile);
        $stats = json_decode($jsonData, true);

        foreach ($stats['players'] as $player) {
            $name = $conn->quote($player['name']);
            $kills = $player['kills'];
            $deaths = $player['deaths'];
            $headshots = $player['headshots'];

            $query = "INSERT INTO players (name, kills, deaths, headshots) 
                      VALUES ($name, $kills, $deaths, $headshots)
                      ON DUPLICATE KEY UPDATE 
                      kills = kills + VALUES(kills), 
                      deaths = deaths + VALUES(deaths), 
                      headshots = headshots + VALUES(headshots)";
            $conn->exec($query);
        }

        // Atualiza o status do arquivo
        $updateQuery = "UPDATE demos SET status = 'processed' WHERE id = :id";
        $updateStmt = $conn->prepare($updateQuery);
        $updateStmt->bindParam(':id', $demo['id']);
        $updateStmt->execute();

        log_message("Demo processada com sucesso: {$filePath}");
    } else {
        // Marca o arquivo como falha
        $updateQuery = "UPDATE demos SET status = 'failed' WHERE id = :id";
        $updateStmt = $conn->prepare($updateQuery);
        $updateStmt->bindParam(':id', $demo['id']);
        $updateStmt->execute();

        log_message("Falha ao processar demo: {$filePath}");
    }
}
?>
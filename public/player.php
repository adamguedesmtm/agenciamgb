<?php
include_once __DIR__ . '/../config/db.php';

if (isset($_GET['nome'])) {
    $nome = $_GET['nome'];
    $query = "SELECT * FROM players WHERE nome = :nome";
    $stmt = $conn->prepare($query);
    $stmt->bindParam(':nome', $nome);
    $stmt->execute();
    $jogador = $stmt->fetch(PDO::FETCH_ASSOC);

    if (!$jogador) {
        die("Jogador não encontrado.");
    }
}
?>

<!DOCTYPE html>
<html lang="pt">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Perfil do Jogador</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <div class="container">
        <h1>Perfil do Jogador: <?= htmlspecialchars($jogador['nome']) ?></h1>
        <p><strong>Kills:</strong> <?= $jogador['kills'] ?></p>
        <p><strong>Mortes:</strong> <?= $jogador['mortes'] ?></p>
        <p><strong>K/D Ratio:</strong> <?= round($jogador['kd_ratio'], 2) ?></p>
        <p><strong>Headshots:</strong> <?= $jogador['headshots'] ?></p>
    </div>
</body>
</html>
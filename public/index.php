<?php
include_once __DIR__ . '/../config/db.php';

$query = "SELECT * FROM players ORDER BY kd_ratio DESC LIMIT 10";
$stmt = $conn->prepare($query);
$stmt->execute();
$top_players = $stmt->fetchAll(PDO::FETCH_ASSOC);
?>

<!DOCTYPE html>
<html lang="pt">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Estatísticas CS2</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <div class="container">
        <h1>Top 10 Jogadores</h1>
        <table>
            <tr>
                <th>Jogador</th>
                <th>Kills</th>
                <th>Mortes</th>
                <th>K/D Ratio</th>
                <th>Headshots</th>
            </tr>
            <?php foreach ($top_players as $player): ?>
            <tr>
                <td><?= htmlspecialchars($player['nome']) ?></td>
                <td><?= $player['kills'] ?></td>
                <td><?= $player['mortes'] ?></td>
                <td><?= round($player['kd_ratio'], 2) ?></td>
                <td><?= $player['headshots'] ?></td>
            </tr>
            <?php endforeach; ?>
        </table>
    </div>
</body>
</html>
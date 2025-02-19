<?php
// public/player.php
// Página individual do jogador com estatísticas e gráficos

include '../config/db.php';

$nome = $_GET['nome'];
$query = "SELECT * FROM players WHERE nome = :nome";
$stmt = $conn->prepare($query);
$stmt->bindParam(':nome', $nome);
$stmt->execute();
$jogador = $stmt->fetch(PDO::FETCH_ASSOC);

if (!$jogador) {
    die("Jogador não encontrado.");
}

// Busca as roles do jogador
$rolesQuery = "SELECT role, emoji FROM roles WHERE user_id = :user_id";
$rolesStmt = $conn->prepare($rolesQuery);
$rolesStmt->bindParam(':user_id', $jogador['id']);
$rolesStmt->execute();
$roles = $rolesStmt->fetchAll(PDO::FETCH_ASSOC);

// Busca os heatmaps do jogador
$heatmapsQuery = "SELECT map_name, heatmap_path FROM heatmaps WHERE player_id = :player_id";
$heatmapsStmt = $conn->prepare($heatmapsQuery);
$heatmapsStmt->bindParam(':player_id', $jogador['id']);
$heatmapsStmt->execute();
$heatmaps = $heatmapsStmt->fetchAll(PDO::FETCH_ASSOC);
?>

<!DOCTYPE html>
<html lang="pt">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Perfil do Jogador</title>
    <link rel="stylesheet" href="style.css">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body>
    <div class="container">
        <h1>Perfil do Jogador: <?= htmlspecialchars($jogador['nome']) ?></h1>
        <p><strong>Kills:</strong> <?= $jogador['kills'] ?></p>
        <p><strong>Mortes:</strong> <?= $jogador['mortes'] ?></p>
        <p><strong>K/D Ratio:</strong> <?= number_format($jogador['kd_ratio'], 2) ?></p>
        <p><strong>Headshots:</strong> <?= $jogador['headshots'] ?></p>

        <h2>Roles</h2>
        <ul>
            <?php foreach ($roles as $role): ?>
            <li><?= htmlspecialchars($role['emoji']) ?> <?= htmlspecialchars($role['role']) ?></li>
            <?php endforeach; ?>
        </ul>

        <h2>Heatmaps</h2>
        <?php if ($heatmaps): ?>
            <ul>
                <?php foreach ($heatmaps as $heatmap): ?>
                <li>
                    <strong>Mapa:</strong> <?= htmlspecialchars($heatmap['map_name']) ?><br>
                    <img src="<?= htmlspecialchars($heatmap['heatmap_path']) ?>" alt="Heatmap de <?= htmlspecialchars($heatmap['map_name']) ?>" style="max-width: 100%; height: auto;">
                </li>
                <?php endforeach; ?>
            </ul>
        <?php else: ?>
            <p>Nenhum heatmap disponível para este jogador.</p>
        <?php endif; ?>

        <h2>Estatísticas ao Longo do Tempo</h2>
        <canvas id="statsChart" width="400" height="200"></canvas>
        <script>
            const ctx = document.getElementById('statsChart').getContext('2d');
            const statsChart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: ['Kills', 'Mortes', 'Headshots'],
                    datasets: [{
                        label: 'Estatísticas',
                        data: [<?= $jogador['kills'] ?>, <?= $jogador['mortes'] ?>, <?= $jogador['headshots'] ?>],
                        backgroundColor: ['#007BFF', '#FF5733', '#28A745'],
                        borderColor: ['#007BFF', '#FF5733', '#28A745'],
                        borderWidth: 1
                    }]
                },
                options: {
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });
        </script>
    </div>
</body>
</html>
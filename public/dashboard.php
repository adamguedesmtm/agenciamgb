<?php
// public/dashboard.php
// Painel administrativo com estatísticas

include '../config/db.php';

$query = "SELECT id, nome, kills, mortes, kd_ratio, headshots, elo FROM players ORDER BY kd_ratio DESC LIMIT 10";
$stmt = $conn->prepare($query);
$stmt->execute();
$jogadores = $stmt->fetchAll(PDO::FETCH_ASSOC);

$query = "SELECT * FROM demos WHERE status = 'processed' ORDER BY id DESC LIMIT 10";
$stmt = $conn->prepare($query);
$stmt->execute();
$demos = $stmt->fetchAll(PDO::FETCH_ASSOC);

$query = "SELECT * FROM active_servers WHERE status = 'running' LIMIT 1";
$stmt = $conn->prepare($query);
$stmt->execute();
$servidorAtivo = $stmt->fetch(PDO::FETCH_ASSOC);
?>

<!DOCTYPE html>
<html lang="pt">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard</title>
    <link rel="stylesheet" href="style.css">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body>
    <div class="container">
        <h1>Dashboard de Estatísticas</h1>

        <h2>Top 10 Jogadores</h2>
        <table>
            <thead>
                <tr>
                    <th>#</th>
                    <th>Jogador</th>
                    <th>Elo</th>
                    <th>Kills</th>
                    <th>Mortes</th>
                    <th>K/D Ratio</th>
                    <th>Headshots</th>
                    <th>Roles</th>
                </tr>
            </thead>
            <tbody>
                <?php foreach ($jogadores as $indice => $jogador): ?>
                <tr>
                    <td><?= $indice + 1 ?></td>
                    <td><?= htmlspecialchars($jogador['nome']) ?></td>
                    <td><?= $jogador['elo'] ?></td>
                    <td><?= $jogador['kills'] ?></td>
                    <td><?= $jogador['mortes'] ?></td>
                    <td><?= number_format($jogador['kd_ratio'], 2) ?></td>
                    <td><?= $jogador['headshots'] ?></td>
                    <td>
                        <?php
                        // Busca as roles do jogador
                        $rolesQuery = "SELECT role, emoji FROM roles WHERE user_id = :user_id";
                        $rolesStmt = $conn->prepare($rolesQuery);
                        $rolesStmt->bindParam(':user_id', $jogador['id']);
                        $rolesStmt->execute();
                        $roles = $rolesStmt->fetchAll(PDO::FETCH_ASSOC);

                        foreach ($roles as $role): ?>
                        <span><?= htmlspecialchars($role['emoji']) ?> <?= htmlspecialchars($role['role']) ?></span><br>
                        <?php endforeach; ?>
                    </td>
                </tr>
                <?php endforeach; ?>
            </tbody>
        </table>

        <h2>Demos Recentes</h2>
        <table>
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Arquivo</th>
                    <th>Status</th>
                    <th>Data de Processamento</th>
                </tr>
            </thead>
            <tbody>
                <?php foreach ($demos as $demo): ?>
                <tr>
                    <td><?= $demo['id'] ?></td>
                    <td><?= htmlspecialchars($demo['file_path']) ?></td>
                    <td><?= htmlspecialchars($demo['status']) ?></td>
                    <td><?= htmlspecialchars($demo['processed_at']) ?></td>
                </tr>
                <?php endforeach; ?>
            </tbody>
        </table>

        <h2>Servidor Ativo</h2>
        <?php if ($servidorAtivo): ?>
            <p>Categoria: <?= htmlspecialchars($servidorAtivo['categoria']) ?></p>
            <p>Status: <?= htmlspecialchars($servidorAtivo['status']) ?></p>
            <p>Placar: <?= htmlspecialchars($servidorAtivo['score']) ?></p>
            <p>Iniciado em: <?= htmlspecialchars($servidorAtivo['started_at']) ?></p>
        <?php else: ?>
            <p>Nenhum servidor ativo.</p>
        <?php endif; ?>

        <h2>Estatísticas Gerais</h2>
        <canvas id="generalChart" width="400" height="200"></canvas>
        <script>
            const ctx = document.getElementById('generalChart').getContext('2d');
            const generalChart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: ['Kills', 'Mortes', 'Headshots'],
                    datasets: [
                        {
                            label: 'Média',
                            data: [<?= array_sum(array_column($jogadores, 'kills')) / count($jogadores) ?>, <?= array_sum(array_column($jogadores, 'mortes')) / count($jogadores) ?>, <?= array_sum(array_column($jogadores, 'headshots')) / count($jogadores) ?>],
                            backgroundColor: ['#007BFF', '#FF5733', '#28A745'],
                            borderColor: ['#007BFF', '#FF5733', '#28A745'],
                            borderWidth: 1
                        }
                    ]
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
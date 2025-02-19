<?php
// public/rankings.php
// Página de ranking global dos jogadores

include '../config/db.php';

$query = "SELECT id, nome, kills, mortes, kd_ratio, headshots, elo FROM players ORDER BY kd_ratio DESC LIMIT 10";
$stmt = $conn->prepare($query);
$stmt->execute();
$jogadores = $stmt->fetchAll(PDO::FETCH_ASSOC);
?>

<!DOCTYPE html>
<html lang="pt">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ranking Global</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <div class="container">
        <h1>Ranking Global</h1>
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

                        foreach ($roles as $role):
                        ?>
                        <span><?= htmlspecialchars($role['emoji']) ?> <?= htmlspecialchars($role['role']) ?></span><br>
                        <?php endforeach; ?>
                    </td>
                </tr>
                <?php endforeach; ?>
            </tbody>
        </table>
    </div>
</body>
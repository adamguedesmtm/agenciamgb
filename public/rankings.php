<?php
// public/rankings.php
// Página de ranking global dos jogadores

// Função para descriptografar uma string
function decrypt_string($encrypted_string, $encryption_key) {
    return shell_exec("echo -n \"$encrypted_string\" | openssl enc -aes-256-cbc -a -d -salt -pass pass:\"$encryption_key\"");
}

// Carregar as credenciais do .env
$dotenv = [];
if (file_exists('../.env')) {
    $dotenv_lines = file('../.env', FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
    foreach ($dotenv_lines as $line) {
        list($key, $value) = explode('=', $line, 2);
        $dotenv[$key] = trim($value);
    }
}

// Descriptografar as credenciais
$encryption_key = $dotenv['ENCRYPTION_KEY'];
$db_host = decrypt_string($dotenv['DB_HOST'], $encryption_key);
$db_name = decrypt_string($dotenv['DB_NAME'], $encryption_key);
$db_user = decrypt_string($dotenv['DB_USER'], $encryption_key);
$db_pass = decrypt_string($dotenv['DB_PASS'], $encryption_key);
$discord_bot_token = decrypt_string($dotenv['DISCORD_BOT_TOKEN'], $encryption_key);
$steam_api_key = decrypt_string($dotenv['STEAM_API_KEY'], $encryption_key);

// Conexão com o banco de dados SQLite
$dbPath = '/var/www/agenciamgb/storage/logs/stats.db';

try {
    $conn = new PDO("sqlite:$dbPath");
    $conn->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
} catch (PDOException $e) {
    echo "Erro na conexão: " . $e->getMessage();
    exit;
}

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

                        foreach ($roles as $role): ?>
                        <span><?= htmlspecialchars($role['emoji']) ?> <?= htmlspecialchars($role['role']) ?></span><br>
                        <?php endforeach; ?>
                    </td>
                </tr>
                <?php endforeach; ?>
            </tbody>
        </table>
    </div>
</body>
</html>
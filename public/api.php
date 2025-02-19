<?php
// public/api.php
// API para retornar estatísticas e outras informações

header("Content-Type: application/json");

require_once __DIR__ . '/../config/db.php';

$action = $_GET['action'] ?? '';

if ($action === 'get_stats') {
    $nome = $_GET['nome'] ?? '';
    if ($nome) {
        try {
            $query = "SELECT * FROM players WHERE nome = :nome";
            $stmt = $conn->prepare($query);
            $stmt->bindParam(':nome', $nome, PDO::PARAM_STR);
            $stmt->execute();
            $jogador = $stmt->fetch(PDO::FETCH_ASSOC);
            echo json_encode($jogador ?: ["erro" => "Jogador não encontrado"]);
        } catch (PDOException $e) {
            echo json_encode(["erro" => "Erro ao buscar estatísticas: " . $e->getMessage()]);
        }
    } else {
        echo json_encode(["erro" => "Nome do jogador não fornecido"]);
    }
} elseif ($action === 'get_rankings') {
    try {
        $query = "SELECT nome, kills, mortes, kd_ratio FROM players ORDER BY kd_ratio DESC LIMIT 10";
        $stmt = $conn->prepare($query);
        $stmt->execute();
        $jogadores = $stmt->fetchAll(PDO::FETCH_ASSOC);
        echo json_encode(["jogadores" => $jogadores]);
    } catch (PDOException $e) {
        echo json_encode(["erro" => "Erro ao buscar rankings: " . $e->getMessage()]);
    }
} else {
    echo json_encode(["erro" => "Ação inválida"]);
}
?>
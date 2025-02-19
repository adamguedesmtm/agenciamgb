<?php
// scripts/process_demos.php
// Script para processar demos em segundo plano usando o CS Demo Manager

include '../config/db.php';
$logFile = '/var/www/agenciamgb/storage/logs/process.log';

function log_message($message, $logFile = '/var/www/agenciamgb/storage/logs/process.log') {
    $timestamp = date('Y-m-d H:i:s');
    file_put_contents($logFile, "[$timestamp] $message\n", FILE_APPEND);
}

$query = "SELECT * FROM demos WHERE status = 'pending' LIMIT 1";
$stmt = $conn->prepare($query);
$stmt->execute();
$demo = $stmt->fetch(PDO::FETCH_ASSOC);

if ($demo) {
    $filePath = $demo['file_path'];
    $outputFile = str_replace('.dem', '.json', $filePath);

    // Processa o arquivo usando CS Demo Manager
    $command = "/usr/local/bin/cs-demo-manager --input {$filePath} --output {$outputFile} --heatmap";
    exec($command, $output, $returnVar);

    if ($returnVar === 0) {
        // Lê o JSON gerado e salva no banco de dados
        $jsonData = file_get_contents($outputFile);
        $stats = json_decode($jsonData, true);

        foreach ($stats['players'] as $player) {
            $nome = $conn->quote($player['name']);
            $kills = $player['kills'];
            $mortes = $player['deaths'];
            $headshots = $player['headshots'];
            $assists = $player['assists'];
            $tactical_kills = $player['tactical_kills'];
            $flank_kills = $player['flank_kills'];
            $entry_kills = $player['entry_kills'];
            $first_seconds_kills = $player['first_seconds_kills'];
            $duels_initiated = $player['duels_initiated'];
            $awp_kills = $player['awp_kills'];
            $awp_purchases = $player['awp_purchases'];
            $headshot_percentage = $player['headshot_percentage'];
            $defensive_multi_kills = $player['defensive_multi_kills'];
            $clutch_wins = $player['clutch_wins'];
            $survival_rate = $player['survival_rate'];
            $grenade_damage = $player['grenade_damage'];
            $blinded_enemies = $player['blinded_enemies'];
            $molotov_damage = $player['molotov_damage'];
            $he_kills = $player['he_kills'];
            $backstab_kills = $player['backstab_kills'];
            $control_zone_kills = $player['control_zone_kills'];
            $stationary_kills = $player['stationary_kills'];
            $rotation_time = $player['rotation_time'];
            $eco_rounds_won = $player['eco_rounds_won'];
            $pistol_rounds_won = $player['pistol_rounds_won'];
            $money_saved = $player['money_saved'];
            $total_damage_taken = $player['total_damage_taken'];
            $lowest_kills = $player['lowest_kills'];
            $bot_eco_deaths = $player['bot_eco_deaths'];
            $first_kill_deaths = $player['first_kill_deaths'];
            $inactive_time = $player['inactive_time'];
            $missed_shots = $player['missed_shots'];
            $clutch_losses = $player['clutch_losses'];
            $last_alive_first_die = $player['last_alive_first_die'];
            $no_trade_deaths = $player['no_trade_deaths'];
            $missed_before_hit = $player['missed_before_hit'];
            $awp_noscope_misses = $player['awp_noscope_misses'];
            $leg_shots = $player['leg_shots'];
            $wasted_shots = $player['wasted_shots'];
            $fake_defuse_deaths = $player['fake_defuse_deaths'];
            $wandering_time = $player['wandering_time'];
            $self_blinded = $player['self_blinded'];
            $teamkills = $player['teamkills'];
            $exploded_by_c4 = $player['exploded_by_c4'];
            $nade_damage_taken = $player['nade_damage_taken'];

            // Busca o ID do jogador no banco de dados
            $playerQuery = "SELECT id FROM players WHERE nome = :nome";
            $playerStmt = $conn->prepare($playerQuery);
            $playerStmt->bindParam(':nome', $player['name']);
            $playerStmt->execute();
            $playerData = $playerStmt->fetch(PDO::FETCH_ASSOC);

            if ($playerData) {
                $playerId = $playerData['id'];
            } else {
                // Insere o jogador no banco de dados se não existir
                $insertPlayerQuery = "INSERT INTO players (nome, steam_id, kills, mortes, headshots, assists, tactical_kills, flank_kills, entry_kills, first_seconds_kills, duels_initiated, awp_kills, awp_purchases, headshot_percentage, defensive_multi_kills, clutch_wins, survival_rate, grenade_damage, blinded_enemies, molotov_damage, he_kills, backstab_kills, control_zone_kills, stationary_kills, rotation_time, eco_rounds_won, pistol_rounds_won, money_saved, total_damage_taken, lowest_kills, bot_eco_deaths, first_kill_deaths, inactive_time, missed_shots, clutch_losses, last_alive_first_die, no_trade_deaths, missed_before_hit, awp_noscope_misses, leg_shots, wasted_shots, fake_defuse_deaths, wandering_time, self_blinded, teamkills, exploded_by_c4, nade_damage_taken) VALUES (:nome, :steam_id, :kills, :mortes, :headshots, :assists, :tactical_kills, :flank_kills, :entry_kills, :first_seconds_kills, :duels_initiated, :awp_kills, :awp_purchases, :headshot_percentage, :defensive_multi_kills, :clutch_wins, :survival_rate, :grenade_damage, :blinded_enemies, :molotov_damage, :he_kills, :backstab_kills, :control_zone_kills, :stationary_kills, :rotation_time, :eco_rounds_won, :pistol_rounds_won, :money_saved, :total_damage_taken, :lowest_kills, :bot_eco_deaths, :first_kill_deaths, :inactive_time, :missed_shots, :clutch_losses, :last_alive_first_die, :no_trade_deaths, :missed_before_hit, :awp_noscope_misses, :leg_shots, :wasted_shots, :fake_defuse_deaths, :wandering_time, :self_blinded, :teamkills, :exploded_by_c4, :nade_damage_taken)";
                $insertPlayerStmt = $conn->prepare($insertPlayerQuery);
                $insertPlayerStmt->bindParam(':nome', $player['name']);
                $insertPlayerStmt->bindParam(':steam_id', $player['steam_id']);
                $insertPlayerStmt->bindParam(':kills', $kills);
                $insertPlayerStmt->bindParam(':mortes', $mortes);
                $insertPlayerStmt->bindParam(':headshots', $headshots);
                $insertPlayerStmt->bindParam(':assists', $assists);
                $insertPlayerStmt->bindParam(':tactical_kills', $tactical_kills);
                $insertPlayerStmt->bindParam(':flank_kills', $flank_kills);
                $insertPlayerStmt->bindParam(':entry_kills', $entry_kills);
                $insertPlayerStmt->bindParam(':first_seconds_kills', $first_seconds_kills);
                $insertPlayerStmt->bindParam(':duels_initiated', $duels_initiated);
                $insertPlayerStmt->bindParam(':awp_kills', $awp_kills);
                $insertPlayerStmt->bindParam(':awp_purchases', $awp_purchases);
                $insertPlayerStmt->bindParam(':headshot_percentage', $headshot_percentage);
                $insertPlayerStmt->bindParam(':defensive_multi_kills', $defensive_multi_kills);
                $insertPlayerStmt->bindParam(':clutch_wins', $clutch_wins);
                $insertPlayerStmt->bindParam(':survival_rate', $survival_rate);
                $insertPlayerStmt->bindParam(':grenade_damage', $grenade_damage);
                $insertPlayerStmt->bindParam(':blinded_enemies', $blinded_enemies);
                $insertPlayerStmt->bindParam(':molotov_damage', $molotov_damage);
                $insertPlayerStmt->bindParam(':he_kills', $he_kills);
                $insertPlayerStmt->bindParam(':backstab_kills', $backstab_kills);
                $insertPlayerStmt->bindParam(':control_zone_kills', $control_zone_kills);
                $insertPlayerStmt->bindParam(':stationary_kills', $stationary_kills);
                $insertPlayerStmt->bindParam(':rotation_time', $rotation_time);
                $insertPlayerStmt->bindParam(':eco_rounds_won', $eco_rounds_won);
                $insertPlayerStmt->bindParam(':pistol_rounds_won', $pistol_rounds_won);
                $insertPlayerStmt->bindParam(':money_saved', $money_saved);
                $insertPlayerStmt->bindParam(':total_damage_taken', $total_damage_taken);
                $insertPlayerStmt->bindParam(':lowest_kills', $lowest_kills);
                $insertPlayerStmt->bindParam(':bot_eco_deaths', $bot_eco_deaths);
                $insertPlayerStmt->bindParam(':first_kill_deaths', $first_kill_deaths);
                $insertPlayerStmt->bindParam(':inactive_time', $inactive_time);
                $insertPlayerStmt->bindParam(':missed_shots', $missed_shots);
                $insertPlayerStmt->bindParam(':clutch_losses', $clutch_losses);
                $insertPlayerStmt->bindParam(':last_alive_first_die', $last_alive_first_die);
                $insertPlayerStmt->bindParam(':no_trade_deaths', $no_trade_deaths);
                $insertPlayerStmt->bindParam(':missed_before_hit', $missed_before_hit);
                $insertPlayerStmt->bindParam(':awp_noscope_misses', $awp_noscope_misses);
                $insertPlayerStmt->bindParam(':leg_shots', $leg_shots);
                $insertPlayerStmt->bindParam(':wasted_shots', $wasted_shots);
                $insertPlayerStmt->bindParam(':fake_defuse_deaths', $fake_defuse_deaths);
                $insertPlayerStmt->bindParam(':wandering_time', $wandering_time);
                $insertPlayerStmt->bindParam(':self_blinded', $self_blinded);
                $insertPlayerStmt->bindParam(':teamkills', $teamkills);
                $insertPlayerStmt->bindParam(':exploded_by_c4', $exploded_by_c4);
                $insertPlayerStmt->bindParam(':nade_damage_taken', $nade_damage_taken);
                $insertPlayerStmt->execute();

                $playerId = $conn->lastInsertId();
                log_message("Jogador inserido no banco de dados: {$player['name']}");
            } else {
                // Atualiza as estatísticas do jogador existente
                $updatePlayerQuery = "UPDATE players SET kills = kills + :kills, mortes = mortes + :mortes, headshots = headshots + :headshots, assists = assists + :assists, tactical_kills = tactical_kills + :tactical_kills, flank_kills = flank_kills + :flank_kills, entry_kills = entry_kills + :entry_kills, first_seconds_kills = first_seconds_kills + :first_seconds_kills, duels_initiated = duels_initiated + :duels_initiated, awp_kills = awp_kills + :awp_kills, awp_purchases = awp_purchases + :awp_purchases, headshot_percentage = :headshot_percentage, defensive_multi_kills = defensive_multi_kills + :defensive_multi_kills, clutch_wins = clutch_wins + :clutch_wins, survival_rate = :survival_rate, grenade_damage = grenade_damage + :grenade_damage, blinded_enemies = blinded_enemies + :blinded_enemies, molotov_damage = molotov_damage + :molotov_damage, he_kills = he_kills + :he_kills, backstab_kills = backstab_kills + :backstab_kills, control_zone_kills = control_zone_kills + :control_zone_kills, stationary_kills = stationary_kills + :stationary_kills, rotation_time = :rotation_time, eco_rounds_won = eco_rounds_won + :eco_rounds_won, pistol_rounds_won = pistol_rounds_won + :pistol_rounds_won, money_saved = :money_saved, total_damage_taken = total_damage_taken + :total_damage_taken, lowest_kills = :lowest_kills, bot_eco_deaths = bot_eco_deaths + :bot_eco_deaths, first_kill_deaths = first_kill_deaths + :first_kill_deaths, inactive_time = :inactive_time, missed_shots = missed_shots + :missed_shots, clutch_losses = clutch_losses + :clutch_losses, last_alive_first_die = :last_alive_first_die, no_trade_deaths = no_trade_deaths + :no_trade_deaths, missed_before_hit = missed_before_hit + :missed_before_hit, awp_noscope_misses = awp_noscope_misses + :awp_noscope_misses, leg_shots = leg_shots + :leg_shots, wasted_shots = wasted_shots + :wasted_shots, fake_defuse_deaths = fake_defuse_deaths + :fake_defuse_deaths, wandering_time = :wandering_time, self_blinded = self_blinded + :self_blinded, teamkills = teamkills + :teamkills, exploded_by_c4 = exploded_by_c4 + :exploded_by_c4, nade_damage_taken = nade_damage_taken + :nade_damage_taken WHERE id = :player_id";
                $updatePlayerStmt = $conn->prepare($updatePlayerQuery);
                $updatePlayerStmt->bindParam(':kills', $kills);
                $updatePlayerStmt->bindParam(':mortes', $mortes);
                $updatePlayerStmt->bindParam(':headshots', $headshots);
                $updatePlayerStmt->bindParam(':assists', $assists);
                $updatePlayerStmt->bindParam(':tactical_kills', $tactical_kills);
                $updatePlayerStmt->bindParam(':flank_kills', $flank_kills);
                $updatePlayerStmt->bindParam(':entry_kills', $entry_kills);
                $updatePlayerStmt->bindParam(':first_seconds_kills', $first_seconds_kills);
                $updatePlayerStmt->bindParam(':duels_initiated', $duels_initiated);
                $updatePlayerStmt->bindParam(':awp_kills', $awp_kills);
                $updatePlayerStmt->bindParam(':awp_purchases', $awp_purchases);
                $updatePlayerStmt->bindParam(':headshot_percentage', $headshot_percentage);
                $updatePlayerStmt->bindParam(':defensive_multi_kills', $defensive_multi_kills);
                $updatePlayerStmt->bindParam(':clutch_wins', $clutch_wins);
                $updatePlayerStmt->bindParam(':survival_rate', $survival_rate);
                $updatePlayerStmt->bindParam(':grenade_damage', $grenade_damage);
                $updatePlayerStmt->bindParam(':blinded_enemies', $blinded_enemies);
                $updatePlayerStmt->bindParam(':molotov_damage', $molotov_damage);
                $updatePlayerStmt->bindParam(':he_kills', $he_kills);
                $updatePlayerStmt->bindParam(':backstab_kills', $backstab_kills);
                $updatePlayerStmt->bindParam(':control_zone_kills', $control_zone_kills);
                $updatePlayerStmt->bindParam(':stationary_kills', $stationary_kills);
                $updatePlayerStmt->bindParam(':rotation_time', $rotation_time);
                $updatePlayerStmt->bindParam(':eco_rounds_won', $eco_rounds_won);
                $updatePlayerStmt->bindParam(':pistol_rounds_won', $pistol_rounds_won);
                $updatePlayerStmt->bindParam(':money_saved', $money_saved);
                $updatePlayerStmt->bindParam(':total_damage_taken', $total_damage_taken);
                $updatePlayerStmt->bindParam(':lowest_kills', $lowest_kills);
                $updatePlayerStmt->bindParam(':bot_eco_deaths', $bot_eco_deaths);
                $updatePlayerStmt->bindParam(':first_kill_deaths', $first_kill_deaths);
                $updatePlayerStmt->bindParam(':inactive_time', $inactive_time);
                $updatePlayerStmt->bindParam(':missed_shots', $missed_shots);
                $updatePlayerStmt->bindParam(':clutch_losses', $clutch_losses);
                $updatePlayerStmt->bindParam(':last_alive_first_die', $last_alive_first_die);
                $updatePlayerStmt->bindParam(':no_trade_deaths', $no_trade_deaths);
                $updatePlayerStmt->bindParam(':missed_before_hit', $missed_before_hit);
                $updatePlayerStmt->bindParam(':awp_noscope_misses', $awp_noscope_misses);
                $updatePlayerStmt->bindParam(':leg_shots', $leg_shots);
                $updatePlayerStmt->bindParam(':wasted_shots', $wasted_shots);
                $updatePlayerStmt->bindParam(':fake_defuse_deaths', $fake_defuse_deaths);
                $updatePlayerStmt->bindParam(':wandering_time', $wandering_time);
                $updatePlayerStmt->bindParam(':self_blinded', $self_blinded);
                $updatePlayerStmt->bindParam(':teamkills', $teamkills);
                $updatePlayerStmt->bindParam(':exploded_by_c4', $exploded_by_c4);
                $updatePlayerStmt->bindParam(':nade_damage_taken', $nade_damage_taken);
                $updatePlayerStmt->bindParam(':player_id', $playerId);
                $updatePlayerStmt->execute();

                log_message("Estatísticas atualizadas para jogador $nome");
            }

            // Insere dados no histórico de jogos
            insert_game_history($demo['id'], $playerId, $player);

            // Atribui roles únicas e genéricas
            assign_unique_roles($playerId, $player['name'], $player);
            assign_generic_roles($playerId, $player['name'], $player);

            // Gera heatmaps para cada mapa jogado
            if (isset($player['heatmaps'])) {
                foreach ($player['heatmaps'] as $map_name => $heatmap_data) {
                    generate_heatmap($playerId, $map_name, $heatmap_data);
                }
            }
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
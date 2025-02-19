<?php
// Simple API to fetch player stats and rankings

if (isset($_GET['player'])) {
    $playerName = $_GET['player'];
    // Fetch player stats from SQLite database
    // Implement player stats fetching logic here
    echo json_encode($playerStats);
} elseif (isset($_GET['rankings'])) {
    // Fetch rankings from SQLite database
    // Implement rankings fetching logic here
    echo json_encode($rankings);
} else {
    echo json_encode(['error' => 'Invalid request']);
}
?>
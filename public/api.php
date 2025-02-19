<?php
include('../config/db.php');
header('Content-Type: application/json');

$db = get_db_connection();

if ($_SERVER['REQUEST_METHOD'] == 'GET') {
    $result = $db->query('SELECT * FROM players');
    $players = [];
    while ($row = $result->fetchArray(SQLITE3_ASSOC)) {
        $players[] = $row;
    }
    echo json_encode($players);
}
?>
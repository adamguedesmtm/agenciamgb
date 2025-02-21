// Main JavaScript file for CS2 Stats
document.addEventListener('DOMContentLoaded', () => {
    fetchRecentMatches();
    fetchTopPlayers();
    setupUploadForm();
});

async function fetchRecentMatches() {
    try {
        const response = await fetch('/api/demos/recent');
        const matches = await response.json();
        
        const container = document.getElementById('recent-matches');
        container.innerHTML = matches.map(match => `
            <div class="bg-gray-700 p-3 rounded mb-2">
                <div class="flex justify-between items-center">
                    <span class="font-bold">${match.map_name}</span>
                    <span>${match.final_score}</span>
                </div>
                <div class="text-sm text-gray-400">
                    ${new Date(match.date).toLocaleString()}
                </div>
            </div>
        `).join('');
    } catch (error) {
        console.error('Erro ao carregar partidas:', error);
    }
}

async function fetchTopPlayers() {
    try {
        const response = await fetch('/api/demos/top-players');
        const players = await response.json();
        
        const container = document.getElementById('top-players');
        container.innerHTML = players.map(player => `
            <div class="bg-gray-700 p-3 rounded mb-2">
                <div class="flex justify-between items-center">
                    <span class="font-bold">${player.name}</span>
                    <span>Rating: ${player.rating}</span>
                </div>
                <div class="text-sm">
                    K/D: ${player.kd_ratio} | HS%: ${player.hs_percentage}%
                </div>
            </div>
        `).join('');
    } catch (error) {
        console.error('Erro ao carregar top players:', error);
    }
}

function setupUploadForm() {
    const form = document.getElementById('upload-form');
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const fileInput = document.getElementById('demo-file');
        const file = fileInput.files[0];
        
        if (!file) {
            alert('Selecione uma demo para upload');
            return;
        }
        
        const formData = new FormData();
        formData.append('demo', file);
        
        try {
            const response = await fetch('/api/demos/upload', {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            
            if (result.success) {
                alert('Demo processada com sucesso!');
                fetchRecentMatches();
            } else {
                alert('Erro ao processar demo: ' + result.message);
            }
        } catch (error) {
            console.error('Erro no upload:', error);
            alert('Erro ao fazer upload da demo');
        }
    });
}
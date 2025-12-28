let tableData = [];

function loadFile() {
    const file = document.getElementById('file').files[0];
    const reader = new FileReader();
    reader.onload = e => {
        const lines = e.target.result.split('\n');
        tableData = lines.map(l => l.split(','));
        renderTable();
    };
    reader.readAsText(file);
}

function renderTable() {
    let html = '<table border=1>';
    tableData.forEach((row, r) => {
        html += '<tr>';
        row.forEach((cell, c) => {
            html += `<td contenteditable oninput="updateCell(${r},${c},this.innerText)">${cell}</td>`;
        });
        html += '</tr>';
    });
    html += '</table>';
    document.getElementById('table').innerHTML = html;
}

function updateCell(r, c, val) {
    tableData[r][c] = val;
    document.getElementById('edited_table').value = JSON.stringify(tableData);
}

function addMessage() {
    const idx = document.querySelectorAll('.msg').length;
    document.getElementById('messages').innerHTML += `
        <div class="msg">
            <textarea name="messages[${idx}][text]" placeholder="Message"></textarea>
            <input type="datetime-local" name="messages[${idx}][datetime]">
        </div>`;
}
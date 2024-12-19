// Função para selecionar ou desmarcar todos os checkboxes
function toggleAllCheckboxes(source) {
    const checkboxes = document.querySelectorAll('.product-checkbox');
    checkboxes.forEach(checkbox => {
        checkbox.checked = source.checked; // Marca ou desmarca com base no "Selecionar Todos"
    });
}

// Função para salvar todos os dados da tabela
function salvarDadosTabela() {
    try {
        const tabela = document.querySelector("table tbody");
        const linhas = tabela.querySelectorAll("tr");
        const dados = [];

        linhas.forEach(linha => {
            const colunas = linha.querySelectorAll("td");
            const produtoId = colunas[0]?.textContent.trim();
            const codigo = colunas[1]?.textContent.trim();
            const nomeComercial = colunas[2]?.querySelector("input")
                ? colunas[2].querySelector("input").value.trim()
                : colunas[2]?.textContent.trim();

            if (produtoId && codigo) {
                dados.push({
                    produto_id: produtoId,
                    codigo: codigo,
                    nome_comercial: nomeComercial
                });
            }
        });

        // Envia os dados para o backend usando fetch
        fetch('/salvar_tabela_produtos', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ produtos: dados }) // Dados em formato JSON
        })
        .then(response => response.json())
        .then(data => {
            console.log(data); // Verifica a resposta do backend
            if (data.status === "success") {
                alert(data.message);
                location.reload(); // Recarrega a página após salvar
            } else {
                alert("Erro ao salvar: " + data.message);
            }
        })
        .catch(error => console.error("Erro ao salvar dados:", error));
    } catch (error) {
        console.error("Erro na função salvarDadosTabela:", error);
    }
}

// Função para aplicar o mesmo valor a todos os produtos selecionados
function aplicarSelecionados(selectElement) {
    try {
        const valorSelecionado = selectElement.value;  // Valor escolhido no campo
        const campoId = selectElement.dataset.campoId; // ID do campo personalizado

        if (!valorSelecionado) {
            alert("Selecione um valor válido para aplicar.");
            return;
        }

        const checkboxesSelecionados = document.querySelectorAll('.product-checkbox:checked');
        if (checkboxesSelecionados.length === 0) {
            alert("Nenhum produto selecionado. Selecione pelo menos um produto.");
            return;
        }

        // Aplica o valor em todos os campos correspondentes
        checkboxesSelecionados.forEach(checkbox => {
            const produtoRow = checkbox.closest('tr');
            const selectCampo = produtoRow.querySelector(`select[data-campo-id="${campoId}"]`);
            if (selectCampo) {
                selectCampo.value = valorSelecionado; // Aplica o valor
            }
        });

        alert("Valores aplicados com sucesso aos produtos selecionados!");
    } catch (error) {
        console.error("Erro na função aplicarSelecionados:", error);
    }
}

// Função para atualizar o nome comercial de todos os produtos
function atualizarNomeComercial() {
    fetch('/atualizar_nome_comercial', {
        method: 'POST'
    })
    .then(() => {
        alert("Nomes comerciais atualizados com sucesso!");
        location.reload(); // Recarrega a página para exibir os dados atualizados
    })
    .catch(error => {
        console.error("Erro ao atualizar nomes comerciais:", error);
        alert("Erro ao atualizar nomes comerciais.");
    });
}



// Requisição para carregar produtos (exemplo de uso)
fetch('/produtos')
    .then(response => response.json())
    .then(data => {
        console.log("Dados recebidos:", data);
        // Lógica para atualizar a tabela na página, se necessário
    })
    .catch(error => console.error("Erro ao carregar os produtos:", error));

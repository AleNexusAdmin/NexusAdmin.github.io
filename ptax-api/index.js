const express = require('express');
const axios = require('axios');
const { create } = require('xmlbuilder2');
const app = express();
const PORT = process.env.PORT || 3000;

// Função para gerar datas no formato MM-DD-YYYY exigido pelo Banco Central
function getDataFormatoBCB(diasAntes = 0) {
    const data = new Date();
    data.setDate(data.getDate() - diasAntes);
    const dia = String(data.getDate()).padStart(2, '0');
    const mes = String(data.getMonth() + 1).padStart(2, '0');
    const ano = data.getFullYear();
    return `${mes}-${dia}-${ano}`;
}

// Função para formatar valores para R$ com vírgula
function formatarBRL(valor) {
    return `R$ ${parseFloat(valor).toFixed(4).replace('.', ',')}`;
}

app.get('/ptax', async (req, res) => {
    try {
        const ontem = getDataFormatoBCB(1);
        const hoje = getDataFormatoBCB(0);

        const url = `https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata/` +
            `CotacaoDolarPeriodo(dataInicial=@dataInicial,dataFinalCotacao=@dataFinalCotacao)` +
            `?@dataInicial='${ontem}'&@dataFinalCotacao='${hoje}'` +
            `&$top=1&$orderby=dataHoraCotacao desc&$format=json&$select=cotacaoCompra,cotacaoVenda,dataHoraCotacao`;

        const response = await axios.get(url);
        const data = response.data.value[0];

        if (!data) return res.status(404).send("Dados não encontrados.");

        const xml = create({ version: '1.0' })
            .ele('Cotacao')
                .ele('DataHora').txt(data.dataHoraCotacao).up()
                .ele('Compra').txt(formatarBRL(data.cotacaoCompra)).up()
                .ele('Venda').txt(formatarBRL(data.cotacaoVenda)).up()
            .end({ prettyPrint: true });

        res.set('Content-Type', 'application/xml');
        res.send(xml);

    } catch (err) {
        console.error(err.message);
        res.status(500).send('Erro ao consultar dólar PTAX');
    }
});

app.listen(PORT, () => {
    console.log("PTAX API rodando na porta " + PORT);
});

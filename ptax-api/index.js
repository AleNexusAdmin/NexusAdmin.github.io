const express = require('express');
const axios = require('axios');
const { create } = require('xmlbuilder2');
const app = express();
const PORT = process.env.PORT || 3000;

app.get('/ptax', async (req, res) => {
    try {
        const url = 'https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata/CotacaoDolarUltimoDia?%24format=json';
        const response = await axios.get(url);
        const data = response.data.value[0];

        const xml = create({ version: '1.0' })
            .ele('Cotacao')
                .ele('DataHora').txt(data.dataHoraCotacao).up()
                .ele('Compra').txt(data.cotacaoCompra).up()
                .ele('Venda').txt(data.cotacaoVenda).up()
            .end({ prettyPrint: true });

        res.set('Content-Type', 'application/xml');
        res.send(xml);

    } catch {
        res.status(500).send('Erro ao consultar dólar PTAX');
    }
});

app.listen(PORT, () => {
    console.log("PTAX API rodando na porta " + PORT);
});
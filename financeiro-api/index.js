const express = require('express');
const axios = require('axios');
const { create } = require('xmlbuilder2');
const app = express();
const PORT = process.env.PORT || 3000;

app.get('/financeiro', async (req, res) => {
    try {
        const response = await axios.get('https://economia.awesomeapi.com.br/last/USD-BRL,BTC-BRL,IBOV');
        const data = response.data;

        const xml = create({ version: '1.0' })
            .ele('Mercado')
                .ele('Dolar')
                    .ele('Compra').txt(data.USDBRL.bid).up()
                    .ele('Venda').txt(data.USDBRL.ask).up()
                .up()
                .ele('Bitcoin')
                    .ele('Compra').txt(data.BTCBRL.bid).up()
                    .ele('Venda').txt(data.BTCBRL.ask).up()
                .up()
            .end({ prettyPrint: true });

        res.set('Content-Type', 'application/xml');
        res.send(xml);

    } catch {
        res.status(500).send('Erro ao consultar dados financeiros');
    }
});

app.listen(PORT, () => {
    console.log("Financeiro API rodando na porta " + PORT);
});
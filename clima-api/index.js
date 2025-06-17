const express = require('express');
const axios = require('axios');
const { create } = require('xmlbuilder2');
const app = express();
const PORT = process.env.PORT || 3000;

app.get('/clima/:cidade', async (req, res) => {
    try {
        const cidade = req.params.cidade;
        const response = await axios.get(`https://wttr.in/${cidade}?format=j1`);
        const data = response.data.current_condition[0];

        const xml = create({ version: '1.0' })
            .ele('Clima')
                .ele('Temperatura').txt(data.temp_C + '°C').up()
                .ele('Descricao').txt(data.weatherDesc[0].value).up()
                .ele('Umidade').txt(data.humidity + '%').up()
            .end({ prettyPrint: true });

        res.set('Content-Type', 'application/xml');
        res.send(xml);

    } catch {
        res.status(500).send('Erro ao consultar clima');
    }
});

app.listen(PORT, () => {
    console.log("Clima API rodando na porta " + PORT);
});
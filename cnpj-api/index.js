const express = require('express');
const axios = require('axios');
const { create } = require('xmlbuilder2');
const app = express();
const PORT = process.env.PORT || 3000;

app.get('/cnpj/:cnpj', async (req, res) => {
    try {
        const { cnpj } = req.params;
        const response = await axios.get(`https://www.receitaws.com.br/v1/cnpj/${cnpj}`);
        const data = response.data;

        const xml = create({ version: '1.0' })
            .ele('Empresa')
                .ele('Nome').txt(data.nome).up()
                .ele('Fantasia').txt(data.fantasia || '').up()
                .ele('CNPJ').txt(data.cnpj).up()
                .ele('Telefone').txt(data.telefone).up()
                .ele('Email').txt(data.email).up()
                .ele('Situacao').txt(data.situacao).up()
                .ele('UF').txt(data.uf).up()
                .ele('Municipio').txt(data.municipio).up()
            .end({ prettyPrint: true });

        res.set('Content-Type', 'application/xml');
        res.send(xml);

    } catch {
        res.status(500).send('Erro ao consultar CNPJ');
    }
});

app.listen(PORT, () => {
    console.log("CNPJ API rodando na porta " + PORT);
});
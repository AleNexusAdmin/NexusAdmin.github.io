const express = require('express');
const axios = require('axios');
const { create } = require('xmlbuilder2');

const app = express();
const PORT = process.env.PORT || 3000;

app.get('/cep/:cep', async (req, res) => {
    const cep = req.params.cep;

    try {
        const response = await axios.get(`https://viacep.com.br/ws/${cep}/json/`);

        if (response.data.erro) {
            return res.status(404).send('CEP não encontrado');
        }

        const xml = create({ version: '1.0' })
            .ele('Endereco')
                .ele('CEP').txt(response.data.cep).up()
                .ele('Logradouro').txt(response.data.logradouro).up()
                .ele('Complemento').txt(response.data.complemento).up()
                .ele('Bairro').txt(response.data.bairro).up()
                .ele('Cidade').txt(response.data.localidade).up()
                .ele('UF').txt(response.data.uf).up()
            .end({ prettyPrint: true });

        res.set('Content-Type', 'application/xml');
        res.send(xml);

    } catch (error) {
        res.status(500).send('Erro ao buscar o CEP');
    }
});

app.listen(PORT, () => {
    console.log(`API rodando em http://localhost:${PORT}`);
});
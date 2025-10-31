const form = document.querySelector('#route-form');
const summary = document.querySelector('#summary');
const typologySelect = document.querySelector('#typology');
const distanceInput = document.querySelector('#distance');
const tollInput = document.querySelector('#toll');
const fuelPriceInput = document.querySelector('#fuelPrice');
const consumptionInput = document.querySelector('#consumption');
const rateInput = document.querySelector('#rate');

const TYPOLOGY_PRESETS = {
  leve: { consumption: 11, rate: 2.2, fuelPrice: 5.5, toll: 30 },
  toco: { consumption: 6.5, rate: 4.4, fuelPrice: 5.8, toll: 65 },
  truck: { consumption: 4.8, rate: 5.1, fuelPrice: 6.0, toll: 92 },
  carreta: { consumption: 3.2, rate: 6.3, fuelPrice: 6.1, toll: 125 },
  bitrem: { consumption: 2.8, rate: 7.1, fuelPrice: 6.2, toll: 148 }
};

function formatCurrency(value) {
  return value.toLocaleString('pt-BR', {
    style: 'currency',
    currency: 'BRL'
  });
}

function applyTypologyPreset() {
  const preset = TYPOLOGY_PRESETS[typologySelect.value];
  if (!distanceInput.value) {
    distanceInput.focus();
  }

  if (preset) {
    if (!fuelPriceInput.value) fuelPriceInput.value = preset.fuelPrice;
    if (!consumptionInput.value) consumptionInput.value = preset.consumption;
    if (!rateInput.value) rateInput.value = preset.rate;
    if (!tollInput.value) tollInput.value = preset.toll;
  }
}

typologySelect.addEventListener('change', applyTypologyPreset);

document.addEventListener('DOMContentLoaded', () => {
  applyTypologyPreset();
  initMap();
});

function buildSummary(data) {
  const { origin, destination, typology, distance, toll, fuelPrice, consumption, rate, baseCost, fuelCost, totalCost } = data;

  const typologyLabel = {
    leve: 'Veículo leve',
    toco: 'Toco',
    truck: 'Truck',
    carreta: 'Carreta',
    bitrem: 'Bitrem'
  }[typology];

  summary.innerHTML = `
    <div class="summary__header">
      <div>
        <h4>Rota ${origin} → ${destination}</h4>
        <p class="breadcrumb">${distance.toFixed(1)} km • ${typologyLabel}</p>
      </div>
      <div class="summary__cost">${formatCurrency(totalCost)}</div>
    </div>
    <div class="summary__items">
      <div class="summary__item">
        <span>Tarifa base (${formatCurrency(rate)} / km)</span>
        <strong>${formatCurrency(baseCost)}</strong>
      </div>
      <div class="summary__item">
        <span>Combustível (${formatCurrency(fuelPrice)} / L)</span>
        <strong>${formatCurrency(fuelCost)}</strong>
      </div>
      <div class="summary__item">
        <span>Pedágios</span>
        <strong>${formatCurrency(toll)}</strong>
      </div>
    </div>
  `;
}

function calculateFreight({ distance, rate, toll, fuelPrice, consumption }) {
  const baseCost = distance * rate;
  const litersNeeded = distance / consumption;
  const fuelCost = litersNeeded * fuelPrice;
  const totalCost = baseCost + fuelCost + toll;

  return { baseCost, fuelCost, totalCost };
}

form.addEventListener('submit', (event) => {
  event.preventDefault();

  const formData = new FormData(form);
  const distance = Number(formData.get('distance'));
  const toll = Number(formData.get('toll')) || 0;
  const fuelPrice = Number(formData.get('fuelPrice')) || 0;
  const consumption = Number(formData.get('consumption')) || 1;
  const rate = Number(formData.get('rate')) || 0;

  const { baseCost, fuelCost, totalCost } = calculateFreight({ distance, rate, toll, fuelPrice, consumption });

  buildSummary({
    origin: formData.get('origin'),
    destination: formData.get('destination'),
    typology: formData.get('typology'),
    distance,
    toll,
    fuelPrice,
    consumption,
    rate,
    baseCost,
    fuelCost,
    totalCost
  });

  updateMapMarkers(formData.get('origin'), formData.get('destination'));
});

let map;
let markersLayer;

function initMap() {
  map = L.map('map').setView([-14.235, -51.9253], 4);

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors'
  }).addTo(map);

  markersLayer = L.layerGroup().addTo(map);
}

function geocodeLocation(location) {
  if (!location) return Promise.resolve(null);

  const url = `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(location)}`;

  return fetch(url, {
    headers: {
      'User-Agent': 'NexusAdminRoutePlanner/1.0 (learning project)'
    }
  })
    .then((response) => response.json())
    .then((results) => {
      if (results && results.length > 0) {
        const { lat, lon, display_name } = results[0];
        return { lat: Number(lat), lon: Number(lon), label: display_name };
      }
      return null;
    })
    .catch(() => null);
}

async function updateMapMarkers(origin, destination) {
  if (!map) return;
  markersLayer.clearLayers();

  const [originData, destinationData] = await Promise.all([
    geocodeLocation(origin),
    geocodeLocation(destination)
  ]);

  const bounds = [];

  if (originData) {
    const marker = L.marker([originData.lat, originData.lon]).bindPopup(`<strong>Origem</strong><br>${originData.label}`);
    marker.addTo(markersLayer);
    bounds.push([originData.lat, originData.lon]);
  }

  if (destinationData) {
    const marker = L.marker([destinationData.lat, destinationData.lon]).bindPopup(`<strong>Destino</strong><br>${destinationData.label}`);
    marker.addTo(markersLayer);
    bounds.push([destinationData.lat, destinationData.lon]);
  }

  if (bounds.length === 2) {
    map.fitBounds(bounds, { padding: [40, 40] });
  } else if (bounds.length === 1) {
    map.setView(bounds[0], 7);
  }
}

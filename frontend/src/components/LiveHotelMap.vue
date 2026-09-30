<script setup>
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'

const props = defineProps({
  latitude: { type: Number, required: true },
  longitude: { type: Number, required: true },
  hotels: { type: Array, required: true },
  selectedHotelId: { type: String, default: '' },
})

const emit = defineEmits(['select'])
const mapElement = ref(null)
const markers = new Map()
let map

function markerIcon(isSelected) {
  return L.divIcon({
    className: '',
    html: `<span class="hotel-map-marker${isSelected ? ' selected' : ''}" aria-hidden="true"></span>`,
    iconAnchor: [11, 11],
    iconSize: [22, 22],
    popupAnchor: [0, -13],
  })
}

function popupContent(hotel) {
  const container = document.createElement('div')
  const name = document.createElement('strong')
  name.textContent = hotel.name || 'Name unavailable'
  container.append(name)

  if (hotel.address) {
    const address = document.createElement('div')
    address.textContent = hotel.address
    container.append(address)
  }

  return container
}

function updateSelectedMarker() {
  for (const [hotelId, marker] of markers) {
    const isSelected = hotelId === props.selectedHotelId
    marker.setIcon(markerIcon(isSelected))
    marker.setZIndexOffset(isSelected ? 1000 : 0)
  }

  const selectedMarker = markers.get(props.selectedHotelId)
  if (selectedMarker) {
    selectedMarker.openPopup()
    map.panTo(selectedMarker.getLatLng())
  }
}

function renderHotels() {
  if (!map) return

  for (const marker of markers.values()) marker.remove()
  markers.clear()

  const center = L.latLng(props.latitude, props.longitude)
  const bounds = L.latLngBounds([center])

  for (const hotel of props.hotels) {
    const marker = L.marker([hotel.latitude, hotel.longitude], {
      icon: markerIcon(hotel.place_id === props.selectedHotelId),
      title: hotel.name || 'Name unavailable',
    })
      .bindPopup(popupContent(hotel))
      .on('click', () => emit('select', hotel.place_id))
      .addTo(map)

    markers.set(hotel.place_id, marker)
    bounds.extend(marker.getLatLng())
  }

  if (props.hotels.length) map.fitBounds(bounds, { maxZoom: 15, padding: [28, 28] })
  else map.setView(center, 13)

  updateSelectedMarker()
  nextTick(() => map.invalidateSize())
}

onMounted(() => {
  map = L.map(mapElement.value, { scrollWheelZoom: false }).setView(
    [props.latitude, props.longitude],
    13,
  )

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution:
      '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    maxZoom: 19,
  }).addTo(map)

  renderHotels()
})

watch(() => [props.latitude, props.longitude, props.hotels], renderHotels, { deep: true })
watch(() => props.selectedHotelId, updateSelectedMarker)

onBeforeUnmount(() => {
  map?.remove()
  map = undefined
  markers.clear()
})
</script>

<template>
  <div
    ref="mapElement"
    class="live-hotel-map"
    role="region"
    aria-label="Map of hotels near the resolved ZIP code"
  ></div>
</template>

<style scoped>
.live-hotel-map {
  width: 100%;
  min-height: 30rem;
  border-radius: 0.5rem;
}

:deep(.hotel-map-marker) {
  display: block;
  width: 22px;
  height: 22px;
  border: 3px solid #fff;
  border-radius: 50% 50% 50% 0;
  background: #2455a6;
  box-shadow: 0 2px 6px rgb(21 44 91 / 38%);
  transform: rotate(-45deg);
}

:deep(.hotel-map-marker.selected) {
  width: 26px;
  height: 26px;
  margin: -2px;
  background: #c44130;
  box-shadow: 0 0 0 4px rgb(242 201 76 / 70%);
}

@media (max-width: 50rem) {
  .live-hotel-map {
    min-height: 22rem;
  }
}
</style>

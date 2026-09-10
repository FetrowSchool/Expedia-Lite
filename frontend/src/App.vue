<script setup>
import { ref } from 'vue'

import { searchStays } from './api/travel'

const city = ref('')
const searchedCity = ref('')
const stays = ref([])
const error = ref('')
const isSearching = ref(false)
const hasSearched = ref(false)

function formatCurrency(value) {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: 0,
  }).format(value)
}

async function submitSearch() {
  const query = city.value.trim()
  error.value = ''
  stays.value = []
  hasSearched.value = false

  if (!query) {
    error.value = 'Enter a city to search for hotel stays.'
    return
  }

  isSearching.value = true

  try {
    const response = await searchStays(query)
    searchedCity.value = response.city
    stays.value = response.stays
    hasSearched.value = true
  } catch (requestError) {
    error.value = requestError.message
  } finally {
    isSearching.value = false
  }
}
</script>

<template>
  <main class="page-shell">
    <section class="app-card" aria-labelledby="app-title">
      <header class="app-header">
        <p class="eyebrow">Travel stay search</p>
        <h1 id="app-title">Expedia Lite</h1>
        <p class="intro">Search available hotel stays by city and compare trip dates and prices.</p>
      </header>

      <form class="search-form" @submit.prevent="submitSearch">
        <label for="city">City</label>
        <div class="search-controls">
          <input
            id="city"
            v-model="city"
            type="search"
            placeholder="Try Boston or State College"
            autocomplete="address-level2"
          />
          <button type="submit" :disabled="isSearching">
            {{ isSearching ? 'Searching…' : 'Search' }}
          </button>
        </div>
      </form>

      <p v-if="error" class="message error-message" role="alert">{{ error }}</p>
      <p v-else-if="hasSearched && stays.length === 0" class="message" aria-live="polite">
        No hotel stays were found for {{ searchedCity }}.
      </p>

      <section v-else-if="stays.length" class="results" aria-labelledby="results-title">
        <div class="results-heading">
          <h2 id="results-title">Available stays in {{ searchedCity }}</h2>
          <p>{{ stays.length }} {{ stays.length === 1 ? 'stay' : 'stays' }} found</p>
        </div>
        <div class="table-wrapper">
          <table>
            <thead>
              <tr>
                <th scope="col">Trip</th>
                <th scope="col">Hotel</th>
                <th scope="col">Location</th>
                <th scope="col">Dates</th>
                <th scope="col">Nights</th>
                <th scope="col">Nightly rate</th>
                <th scope="col">Stay price</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="stay in stays" :key="stay.trip_id">
                <td>{{ stay.trip_name }}</td>
                <td>{{ stay.hotel_name }}</td>
                <td>{{ stay.city }}, {{ stay.state }}</td>
                <td>{{ stay.check_in }} to {{ stay.check_out }}</td>
                <td>{{ stay.nights }}</td>
                <td>{{ formatCurrency(stay.nightly_rate_usd) }}</td>
                <td>{{ formatCurrency(stay.stay_price_usd) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </section>
  </main>
</template>

<style scoped>
:global(*) {
  box-sizing: border-box;
}

:global(body) {
  margin: 0;
  color: #182230;
  font-family: Inter, ui-sans-serif, system-ui, sans-serif;
  background: #f3f6fb;
}

.page-shell {
  min-height: 100vh;
  padding: clamp(2rem, 6vw, 4rem) 1rem;
}

.app-card {
  width: min(100%, 72rem);
  margin: 0 auto;
  padding: clamp(1.25rem, 4vw, 2.5rem);
  border: 1px solid #d7dfeb;
  border-radius: 0.75rem;
  background: #fff;
  box-shadow: 0 0.75rem 2rem rgb(31 55 90 / 8%);
}

.app-header {
  max-width: 42rem;
}

.eyebrow {
  margin: 0 0 0.5rem;
  color: #2855a6;
  font-size: 0.78rem;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
}

h1 {
  margin: 0 0 0.625rem;
  color: #152c5b;
  font-size: clamp(2rem, 6vw, 3rem);
  line-height: 1.05;
}

.intro {
  margin: 0;
  color: #526173;
  line-height: 1.6;
}

.search-form {
  display: grid;
  gap: 0.625rem;
  margin-top: 2rem;
  padding: 1.25rem;
  border: 1px solid #dbe3ef;
  border-radius: 0.625rem;
  background: #f8faff;
}

label,
h2 {
  font-weight: 700;
}

.search-controls {
  display: flex;
  gap: 0.75rem;
}

input,
button {
  min-height: 3rem;
  border-radius: 0.375rem;
  font: inherit;
}

input {
  width: 100%;
  padding: 0.7rem 0.875rem;
  border: 1px solid #8e9bae;
  color: inherit;
  background: #fff;
}

input::placeholder {
  color: #66758a;
}

button:active:not(:disabled) {
  transform: translateY(1px);
}

button:disabled {
  cursor: wait;
  opacity: 0.65;
}

button {
  min-width: 7rem;
  padding: 0.7rem 1.5rem;
  border: 1px solid #2455a6;
  color: #fff;
  font-weight: 700;
  cursor: pointer;
  background: #2455a6;
}

button:hover:not(:disabled) {
  background: #173f85;
}

input:focus-visible,
button:focus-visible {
  outline: 3px solid #f2c94c;
  outline-offset: 2px;
}

.message {
  margin: 1.5rem 0 0;
  padding: 1rem;
  border: 1px solid #b9c9df;
  border-radius: 0.375rem;
  color: #263c5a;
  background: #f3f7fd;
}

.error-message {
  border-color: #e3b5ae;
  color: #8a2d21;
  background: #fff4f2;
}

.results {
  margin-top: 2rem;
}

.results-heading {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 0.875rem;
}

.results-heading h2,
.results-heading p {
  margin: 0;
}

.results-heading h2 {
  color: #152c5b;
  font-size: 1.25rem;
}

.results-heading p {
  color: #5c6b7d;
  white-space: nowrap;
}

.table-wrapper {
  overflow-x: auto;
  border: 1px solid #ccd6e3;
  border-radius: 0.375rem;
}

table {
  width: 100%;
  min-width: 52rem;
  border-collapse: collapse;
  font-size: 0.92rem;
}

th,
td {
  padding: 0.875rem;
  border-bottom: 1px solid #e0e6ee;
  text-align: left;
  vertical-align: top;
}

th {
  color: #fff;
  font-size: 0.82rem;
  letter-spacing: 0.02em;
  background: #243b64;
}

tbody tr:nth-child(even) {
  background: #f6f8fb;
}

tbody tr:last-child td {
  border-bottom: 0;
}

@media (max-width: 34rem) {
  .search-controls {
    flex-direction: column;
  }

  .results-heading {
    align-items: flex-start;
    flex-direction: column;
    gap: 0.25rem;
  }

  button {
    width: 100%;
  }
}
</style>

<script setup>
import { onMounted, ref } from 'vue'

import {
  cancelBooking,
  createAccount,
  createBooking,
  deleteBooking,
  getBookings,
  getCurrentAccount,
  getUsers,
  loginAccount,
  logoutAccount,
  searchStays,
} from './api/travel'

const city = ref('')
const searchedCity = ref('')
const stays = ref([])
const error = ref('')
const isSearching = ref(false)
const hasSearched = ref(false)
const users = ref([])
const selectedStay = ref(null)
const selectedUserId = ref('')
const bookingMessage = ref('')
const bookingError = ref('')
const isBooking = ref(false)
const bookings = ref([])
const historyError = ref('')
const isLoadingHistory = ref(true)
const cancellingBookingId = ref('')
const deletingBookingId = ref('')
const historyMessage = ref('')
const activeView = ref('search')
const isMenuOpen = ref(false)
const currentAccount = ref(null)
const accountUsername = ref('')
const accountPassword = ref('')
const accountEmail = ref('')
const loginUsername = ref('')
const loginPassword = ref('')
const accountMessage = ref('')
const accountError = ref('')
const isSubmittingAccount = ref(false)

onMounted(async () => {
  try {
    currentAccount.value = await getCurrentAccount()
  } catch (requestError) {
    accountError.value = requestError.message
  }

  try {
    users.value = await getUsers()
    selectedUserId.value = users.value[0]?.user_id || ''
  } catch (requestError) {
    bookingError.value = requestError.message
  }

  await loadBookingHistory()
})

function formatCurrency(value) {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: 0,
  }).format(value)
}

function showView(view) {
  activeView.value = view
  isMenuOpen.value = false
}

async function submitAccountCreation() {
  accountMessage.value = ''
  accountError.value = ''
  const username = accountUsername.value.trim()
  const password = accountPassword.value.trim()

  if (!username || !password) {
    accountError.value = 'Enter a username and password.'
    return
  }

  isSubmittingAccount.value = true
  try {
    const account = await createAccount(username, password, accountEmail.value.trim())
    accountMessage.value = `Account ${account.username} was created. You can now log in.`
    loginUsername.value = account.username
    accountUsername.value = ''
    accountPassword.value = ''
    accountEmail.value = ''
  } catch (requestError) {
    accountError.value = requestError.message
  } finally {
    isSubmittingAccount.value = false
  }
}

async function submitLogin() {
  accountMessage.value = ''
  accountError.value = ''
  const username = loginUsername.value.trim()
  const password = loginPassword.value

  if (!username || !password.trim()) {
    accountError.value = 'Enter your username and password.'
    return
  }

  isSubmittingAccount.value = true
  try {
    currentAccount.value = await loginAccount(username, password)
    accountMessage.value = `Signed in as ${currentAccount.value.username}.`
    loginPassword.value = ''
  } catch (requestError) {
    accountError.value = requestError.message
  } finally {
    isSubmittingAccount.value = false
  }
}

async function submitLogout() {
  accountMessage.value = ''
  accountError.value = ''
  try {
    await logoutAccount()
    currentAccount.value = null
    accountMessage.value = 'You are now logged out.'
  } catch (requestError) {
    accountError.value = requestError.message
  }
}

async function submitSearch() {
  const query = city.value.trim()
  error.value = ''
  stays.value = []
  hasSearched.value = false
  selectedStay.value = null
  bookingMessage.value = ''
  bookingError.value = ''

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

function selectStay(stay) {
  selectedStay.value = stay
  bookingMessage.value = ''
  bookingError.value = ''
}

async function loadBookingHistory() {
  historyError.value = ''
  isLoadingHistory.value = true

  try {
    bookings.value = await getBookings()
  } catch (requestError) {
    historyError.value = requestError.message
  } finally {
    isLoadingHistory.value = false
  }
}

async function submitCancellation(booking) {
  historyMessage.value = ''
  historyError.value = ''
  cancellingBookingId.value = booking.booking_id

  try {
    await cancelBooking(booking.booking_id)
    historyMessage.value = `Booking ${booking.booking_id} was cancelled.`
    await loadBookingHistory()
  } catch (requestError) {
    historyError.value = requestError.message
  } finally {
    cancellingBookingId.value = ''
  }
}

async function submitDeletion(booking) {
  const shouldDelete = window.confirm(
    `Delete booking ${booking.booking_id}? This cannot be undone.`,
  )
  if (!shouldDelete) return

  historyMessage.value = ''
  historyError.value = ''
  deletingBookingId.value = booking.booking_id

  try {
    await deleteBooking(booking.booking_id)
    historyMessage.value = `Booking ${booking.booking_id} was deleted.`
    await loadBookingHistory()
  } catch (requestError) {
    historyError.value = requestError.message
  } finally {
    deletingBookingId.value = ''
  }
}

async function submitBooking() {
  bookingMessage.value = ''
  bookingError.value = ''

  if (!selectedStay.value || !selectedUserId.value) {
    bookingError.value = 'Select a stay and traveler before booking.'
    return
  }

  isBooking.value = true

  try {
    const booking = await createBooking(selectedUserId.value, selectedStay.value.trip_id)
    bookingMessage.value = `Booking ${booking.booking_id} confirmed for ${selectedStay.value.hotel_name}.`
    await loadBookingHistory()
  } catch (requestError) {
    bookingError.value = requestError.message
  } finally {
    isBooking.value = false
  }
}
</script>

<template>
  <main class="page-shell">
    <nav class="top-nav" aria-label="Primary navigation">
      <button class="brand" type="button" @click="showView('search')">
        <span class="brand-mark" aria-hidden="true">E</span>
        <span>Expedia Lite</span>
      </button>

      <div class="nav-tabs" aria-label="Application pages">
        <button
          class="nav-tab"
          :class="{ active: activeView === 'search' }"
          type="button"
          @click="showView('search')"
        >
          Search stays
        </button>
        <button
          class="nav-tab"
          :class="{ active: activeView === 'bookings' }"
          type="button"
          @click="showView('bookings')"
        >
          Bookings
        </button>
        <button
          class="nav-tab"
          :class="{ active: activeView === 'account' }"
          type="button"
          @click="showView('account')"
        >
          Account
        </button>
      </div>

      <div class="menu-wrap">
        <span v-if="currentAccount" class="signed-in-label">
          {{ currentAccount.username }}
        </span>
        <button
          class="menu-button"
          type="button"
          aria-label="Menu"
          :aria-expanded="isMenuOpen"
          aria-controls="app-menu"
          @click="isMenuOpen = !isMenuOpen"
        >
          <span aria-hidden="true"></span>
          <span aria-hidden="true"></span>
          <span aria-hidden="true"></span>
        </button>
        <div v-if="isMenuOpen" id="app-menu" class="menu-panel">
          <p>Menu</p>
          <button type="button" @click="showView('search')">Search stays</button>
          <button type="button" @click="showView('bookings')">Bookings</button>
          <button type="button" @click="showView('account')">Account</button>
        </div>
      </div>
    </nav>

    <section class="app-card" aria-labelledby="app-title">
      <header v-if="activeView === 'search'" class="app-header">
        <p class="eyebrow">Travel stay search</p>
        <h1 id="app-title">Expedia Lite</h1>
        <p class="intro">Search available hotel stays by city and compare trip dates and prices.</p>
      </header>

      <form v-if="activeView === 'search'" class="search-form" @submit.prevent="submitSearch">
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

      <p v-if="activeView === 'search' && error" class="message error-message" role="alert">
        {{ error }}
      </p>
      <p
        v-else-if="activeView === 'search' && hasSearched && stays.length === 0"
        class="message"
        aria-live="polite"
      >
        No hotel stays were found for {{ searchedCity }}.
      </p>

      <section
        v-else-if="activeView === 'search' && stays.length"
        class="results"
        aria-labelledby="results-title"
      >
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
                <th scope="col">Action</th>
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
                <td>
                  <button class="select-button" type="button" @click="selectStay(stay)">
                    {{ selectedStay?.trip_id === stay.trip_id ? 'Selected' : 'Select' }}
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <section
        v-if="activeView === 'search' && selectedStay"
        class="booking-panel"
        aria-labelledby="booking-title"
      >
        <div>
          <p class="eyebrow">Selected stay</p>
          <h2 id="booking-title">Book {{ selectedStay.hotel_name }}</h2>
          <p class="booking-summary">
            {{ selectedStay.trip_name }} · {{ selectedStay.check_in }} to
            {{ selectedStay.check_out }} · {{ formatCurrency(selectedStay.stay_price_usd) }}
          </p>
        </div>

        <form class="booking-form" @submit.prevent="submitBooking">
          <label for="traveler">Traveler</label>
          <div class="booking-controls">
            <select id="traveler" v-model="selectedUserId" :disabled="isBooking || !users.length">
              <option value="" disabled>Select a traveler</option>
              <option v-for="user in users" :key="user.user_id" :value="user.user_id">
                {{ user.display_name }} ({{ user.user_id }})
              </option>
            </select>
            <button type="submit" :disabled="isBooking || !selectedUserId">
              {{ isBooking ? 'Booking…' : 'Book stay' }}
            </button>
          </div>
        </form>

        <p v-if="bookingError" class="message error-message" role="alert">
          {{ bookingError }}
        </p>
        <p v-if="bookingMessage" class="message success-message" role="status">
          {{ bookingMessage }}
        </p>
      </section>

      <section v-if="activeView === 'account'" class="account-view" aria-labelledby="app-title">
        <div class="account-heading">
          <p class="eyebrow">Demo account</p>
          <h1 id="app-title">Account</h1>
          <p class="intro">Use made-up classroom credentials only.</p>
        </div>

        <div v-if="currentAccount" class="signed-in-panel">
          <p class="eyebrow">Signed in</p>
          <h2>{{ currentAccount.username }}</h2>
          <p>User ID: {{ currentAccount.user_id }}</p>
          <button type="button" @click="submitLogout">Log out</button>
        </div>

        <div v-else class="account-grid">
          <form class="account-form" @submit.prevent="submitLogin">
            <div>
              <p class="eyebrow">Existing account</p>
              <h2>Log in</h2>
            </div>
            <label for="login-username">Username</label>
            <input id="login-username" v-model="loginUsername" autocomplete="username" />
            <label for="login-password">Password</label>
            <input
              id="login-password"
              v-model="loginPassword"
              type="password"
              autocomplete="current-password"
            />
            <button type="submit" :disabled="isSubmittingAccount">Log in</button>
          </form>

          <form class="account-form" @submit.prevent="submitAccountCreation">
            <div>
              <p class="eyebrow">New demo account</p>
              <h2>Create account</h2>
            </div>
            <label for="account-username">Username</label>
            <input id="account-username" v-model="accountUsername" autocomplete="username" />
            <label for="account-password">Password</label>
            <input
              id="account-password"
              v-model="accountPassword"
              type="password"
              autocomplete="new-password"
            />
            <label for="account-email">Email <span>(optional)</span></label>
            <input id="account-email" v-model="accountEmail" type="email" autocomplete="email" />
            <button type="submit" :disabled="isSubmittingAccount">Create account</button>
          </form>
        </div>

        <p v-if="accountError" class="message error-message" role="alert">
          {{ accountError }}
        </p>
        <p v-if="accountMessage" class="message success-message" role="status">
          {{ accountMessage }}
        </p>
      </section>

      <section v-if="activeView === 'bookings'" class="history" aria-labelledby="history-title">
        <div class="results-heading">
          <div>
            <p class="eyebrow">Your trips</p>
            <h1 id="app-title">Bookings</h1>
            <h2 id="history-title" class="visually-hidden">Booking history</h2>
          </div>
          <p v-if="bookings.length">{{ bookings.length }} bookings</p>
        </div>

        <p v-if="isLoadingHistory" class="message" role="status">Loading booking history…</p>
        <p v-else-if="historyError" class="message error-message" role="alert">
          {{ historyError }}
        </p>
        <p v-else-if="bookings.length === 0" class="message">No bookings have been made yet.</p>

        <div v-else class="table-wrapper">
          <table>
            <thead>
              <tr>
                <th scope="col">Booking</th>
                <th scope="col">Traveler</th>
                <th scope="col">Trip</th>
                <th scope="col">Hotel</th>
                <th scope="col">Location</th>
                <th scope="col">Booked on</th>
                <th scope="col">Status</th>
                <th scope="col">Action</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="booking in bookings" :key="booking.booking_id">
                <td>{{ booking.booking_id }}</td>
                <td>{{ booking.display_name }} ({{ booking.user_id }})</td>
                <td>{{ booking.trip_name }} ({{ booking.trip_id }})</td>
                <td>{{ booking.hotel_name }}</td>
                <td>{{ booking.city }}, {{ booking.state }}</td>
                <td>{{ booking.booked_on }}</td>
                <td>
                  <span class="status-badge" :class="`status-${booking.status}`">
                    {{ booking.status }}
                  </span>
                </td>
                <td>
                  <div class="booking-actions">
                    <button
                      v-if="booking.status !== 'cancelled'"
                      class="cancel-button"
                      type="button"
                      :disabled="cancellingBookingId === booking.booking_id"
                      @click="submitCancellation(booking)"
                    >
                      {{ cancellingBookingId === booking.booking_id ? 'Cancelling…' : 'Cancel' }}
                    </button>
                    <span v-else class="action-complete">Cancelled</span>
                    <button
                      class="delete-button"
                      type="button"
                      :disabled="deletingBookingId === booking.booking_id"
                      @click="submitDeletion(booking)"
                    >
                      {{ deletingBookingId === booking.booking_id ? 'Deleting…' : 'Delete' }}
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <p v-if="historyMessage" class="message success-message" role="status">
          {{ historyMessage }}
        </p>
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
  padding: 0 1rem clamp(2rem, 6vw, 4rem);
}

.top-nav {
  position: relative;
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  align-items: center;
  width: min(100%, 72rem);
  min-height: 5rem;
  margin: 0 auto 1.5rem;
  border-bottom: 1px solid #d7dfeb;
}

.brand,
.nav-tab,
.menu-button,
.menu-panel button {
  min-width: 0;
  border: 0;
  color: #152c5b;
  background: transparent;
}

.brand {
  display: inline-flex;
  align-items: center;
  justify-self: start;
  gap: 0.65rem;
  padding: 0;
  font-size: 1.25rem;
  letter-spacing: -0.02em;
}

.brand:hover:not(:disabled),
.nav-tab:hover:not(:disabled),
.menu-button:hover:not(:disabled),
.menu-panel button:hover:not(:disabled) {
  color: #173f85;
  background: #edf3fc;
}

.brand-mark {
  display: grid;
  width: 2.25rem;
  height: 2.25rem;
  border-radius: 0.55rem 0.55rem 0.2rem 0.55rem;
  color: #fff;
  font-size: 1.4rem;
  font-weight: 800;
  place-items: center;
  background: #2455a6;
}

.nav-tabs {
  display: flex;
  align-self: stretch;
  gap: 0.25rem;
}

.nav-tab {
  position: relative;
  min-height: auto;
  padding: 0.5rem 1rem;
  border-radius: 0;
}

.nav-tab.active::after {
  position: absolute;
  right: 1rem;
  bottom: -1px;
  left: 1rem;
  height: 3px;
  border-radius: 3px 3px 0 0;
  background: #2455a6;
  content: '';
}

.menu-wrap {
  position: relative;
  display: flex;
  align-items: center;
  justify-self: end;
  gap: 0.5rem;
}

.signed-in-label {
  max-width: 10rem;
  overflow: hidden;
  color: #526173;
  font-size: 0.88rem;
  font-weight: 700;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.menu-button {
  display: grid;
  width: 3rem;
  height: 3rem;
  padding: 0.75rem;
  place-content: center;
  gap: 0.25rem;
}

.menu-button span {
  display: block;
  width: 1.4rem;
  height: 2px;
  border-radius: 2px;
  background: currentColor;
}

.menu-panel {
  position: absolute;
  z-index: 10;
  top: calc(100% + 0.5rem);
  right: 0;
  width: 13rem;
  padding: 0.5rem;
  border: 1px solid #d7dfeb;
  border-radius: 0.625rem;
  background: #fff;
  box-shadow: 0 0.75rem 2rem rgb(31 55 90 / 16%);
}

.menu-panel p {
  margin: 0;
  padding: 0.65rem 0.75rem 0.4rem;
  color: #526173;
  font-size: 0.78rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.menu-panel button {
  width: 100%;
  min-height: 2.75rem;
  padding: 0.6rem 0.75rem;
  text-align: left;
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
button,
select {
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

select {
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
button:focus-visible,
select:focus-visible {
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

.success-message {
  border-color: #9bc8aa;
  color: #175c2f;
  background: #f0faf3;
}

.results {
  margin-top: 2rem;
}

.history {
  margin-top: 0;
}

.visually-hidden {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
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
  min-width: 59rem;
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

.select-button {
  min-width: 5.5rem;
  min-height: 2.25rem;
  padding: 0.4rem 0.75rem;
  border-color: #8391a5;
  color: #223550;
  background: #fff;
}

.select-button:hover:not(:disabled) {
  background: #edf2f8;
}

.booking-panel {
  display: grid;
  gap: 1rem;
  margin-top: 2rem;
  padding: 1.25rem;
  border: 1px solid #b9c9df;
  border-radius: 0.625rem;
  background: #f8faff;
}

.booking-panel h2,
.booking-summary {
  margin: 0;
}

.account-view {
  display: grid;
  gap: 1.5rem;
}

.account-heading {
  max-width: 42rem;
}

.account-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1rem;
}

.account-form,
.signed-in-panel {
  display: grid;
  align-content: start;
  gap: 0.625rem;
  padding: 1.25rem;
  border: 1px solid #dbe3ef;
  border-radius: 0.625rem;
  background: #f8faff;
}

.account-form h2,
.signed-in-panel h2,
.signed-in-panel p {
  margin: 0;
}

.account-form label span {
  color: #66758a;
  font-weight: 400;
}

.booking-summary {
  margin-top: 0.4rem;
  color: #526173;
}

.booking-form {
  display: grid;
  gap: 0.625rem;
}

.booking-controls {
  display: flex;
  gap: 0.75rem;
}

.status-badge {
  display: inline-block;
  padding: 0.25rem 0.5rem;
  border-radius: 999px;
  color: #173f2a;
  font-size: 0.78rem;
  font-weight: 700;
  text-transform: capitalize;
  background: #dff3e5;
}

.status-cancelled {
  color: #7a3329;
  background: #f9e3df;
}

.cancel-button {
  min-width: 5.5rem;
  min-height: 2.25rem;
  padding: 0.4rem 0.75rem;
  border-color: #b14a3c;
  color: #8a2d21;
  background: #fff;
}

.booking-actions {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.cancel-button:hover:not(:disabled) {
  color: #fff;
  background: #9e3d31;
}

.delete-button {
  min-width: 5.5rem;
  min-height: 2.25rem;
  padding: 0.4rem 0.75rem;
  border-color: #802c24;
  color: #fff;
  background: #802c24;
}

.delete-button:hover:not(:disabled) {
  background: #641f1a;
}

.action-complete {
  color: #6b7584;
  font-size: 0.82rem;
}

@media (max-width: 34rem) {
  .top-nav {
    grid-template-columns: 1fr auto;
  }

  .nav-tabs {
    grid-column: 1 / -1;
    grid-row: 2;
    justify-content: stretch;
    width: 100%;
    border-top: 1px solid #e5eaf1;
  }

  .nav-tab {
    flex: 1;
    width: auto;
  }

  .signed-in-label {
    display: none;
  }

  .search-controls {
    flex-direction: column;
  }

  .booking-controls {
    flex-direction: column;
  }

  .account-grid {
    grid-template-columns: 1fr;
  }

  .results-heading {
    align-items: flex-start;
    flex-direction: column;
    gap: 0.25rem;
  }

  button {
    width: 100%;
  }

  .brand,
  .menu-button {
    width: auto;
  }
}
</style>

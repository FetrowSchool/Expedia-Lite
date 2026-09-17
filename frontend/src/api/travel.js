export async function searchStays(city) {
  const response = await fetch(`/api/stays?${new URLSearchParams({ city })}`)
  const payload = await response.json().catch(() => ({}))

  if (!response.ok) {
    throw new Error(payload.detail || 'Unable to search for hotel stays.')
  }

  return payload
}

export async function getUsers() {
  const response = await fetch('/api/users')
  const payload = await response.json().catch(() => ([]))

  if (!response.ok) {
    throw new Error('Unable to load travelers.')
  }

  return payload
}

export async function createBooking(userId, tripId) {
  const response = await fetch('/api/bookings', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ user_id: userId, trip_id: tripId }),
  })
  const payload = await response.json().catch(() => ({}))

  if (!response.ok) {
    throw new Error(payload.detail || 'Unable to create the booking.')
  }

  return payload
}

export async function getBookings() {
  const response = await fetch('/api/bookings')
  const payload = await response.json().catch(() => ([]))

  if (!response.ok) {
    throw new Error('Unable to load booking history.')
  }

  return payload
}

export async function cancelBooking(bookingId) {
  const response = await fetch(`/api/bookings/${encodeURIComponent(bookingId)}/cancel`, {
    method: 'PATCH',
  })
  const payload = await response.json().catch(() => ({}))

  if (!response.ok) {
    throw new Error(payload.detail || 'Unable to cancel the booking.')
  }

  return payload
}

export async function deleteBooking(bookingId) {
  const response = await fetch(`/api/bookings/${encodeURIComponent(bookingId)}`, {
    method: 'DELETE',
  })

  if (!response.ok) {
    const payload = await response.json().catch(() => ({}))
    throw new Error(payload.detail || 'Unable to delete the booking.')
  }
}

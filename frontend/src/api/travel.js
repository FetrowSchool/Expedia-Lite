export async function searchStays(city) {
  const response = await fetch(`/api/stays?${new URLSearchParams({ city })}`)
  const payload = await response.json().catch(() => ({}))

  if (!response.ok) {
    throw new Error(payload.detail || 'Unable to search for hotel stays.')
  }

  return payload
}

export async function requestCalculation({ left, right, operation }) {
  const query = new URLSearchParams({ a: String(left), b: String(right) })
  const response = await fetch(`/${operation}?${query}`)

  const payload = await response.json().catch(() => ({}))

  if (!response.ok) {
    throw new Error(payload.detail || 'The calculation could not be completed.')
  }

  return payload.result
}

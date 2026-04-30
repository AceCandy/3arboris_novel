export function countAlphaNumericHan(text: string | null | undefined): number {
  if (!text) return 0
  const matches = text.match(/[A-Za-z0-9㐀-䶿一-鿿豈-﫿]/g)
  return matches ? matches.length : 0
}

export function countNonWhitespaceChars(text: string | null | undefined): number {
  if (!text) return 0
  return text.replace(/\s/g, '').length
}

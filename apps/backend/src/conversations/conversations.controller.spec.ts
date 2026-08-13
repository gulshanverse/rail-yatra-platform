describe('Response Normalization Test', () => {
  function normalizeAssistantText(rawText: string): string {
    if (!rawText) return '';
    let text = rawText.trim();
    if (
      (text.startsWith('[') && text.endsWith(']')) ||
      (text.startsWith('{') && text.endsWith('}'))
    ) {
      try {
        const jsonish = text
          .replace(/'/g, '"')
          .replace(/None/g, 'null')
          .replace(/True/g, 'true')
          .replace(/False/g, 'false');
        const parsed: unknown = JSON.parse(jsonish);
        if (Array.isArray(parsed)) {
          const parts = parsed
            .map((item: unknown) => {
              if (typeof item === 'object' && item !== null) {
                const rec = item as Record<string, unknown>;
                const val = rec.text ?? rec.reply ?? rec.content ?? '';
                return typeof val === 'string' ? val : JSON.stringify(val);
              }
              return typeof item === 'string' ? item : JSON.stringify(item);
            })
            .filter(Boolean);
          if (parts.length > 0) text = parts.join('\n\n');
        } else if (typeof parsed === 'object' && parsed !== null) {
          const pObj = parsed as Record<string, unknown>;
          if (typeof pObj.text === 'string') text = pObj.text;
          else if (typeof pObj.reply === 'string') text = pObj.reply;
          else if (typeof pObj.content === 'string') text = pObj.content;
        }
      } catch {
        const textMatch =
          /'text':\s*'([\s\S]+?)'(?:,\s*'extras'|,\s*'signature'|\})/g.exec(
            text,
          );
        if (textMatch && textMatch[1]) {
          text = textMatch[1].replace(/\\n/g, '\n').replace(/\\'/g, "'");
        }
      }
    }
    return text;
  }

  it('normalizes plain text correctly', () => {
    const text = 'Here are the train options from Bilaspur to Delhi';
    expect(normalizeAssistantText(text)).toBe(text);
  });

  it('extracts clean text from raw Python repr list with extras and signature', () => {
    const rawRepr =
      "[{'type': 'text', 'text': 'Clean assistant answer text', 'extras': {'signature': 'secret_sig_123'}}]";
    const normalized = normalizeAssistantText(rawRepr);
    expect(normalized).toBe('Clean assistant answer text');
    expect(normalized).not.toContain('extras');
    expect(normalized).not.toContain('signature');
    expect(normalized).not.toContain('secret_sig_123');
  });

  it('handles empty or malformed strings gracefully', () => {
    expect(normalizeAssistantText('')).toBe('');
    expect(normalizeAssistantText('   ')).toBe('');
  });
});

export function formatXml(xml: string): string {
  const lines = xml
    .replace(/>\s*</g, '>\n<') // Ensure each tag is on its own line
    .trim()
    .split('\n');

  let indent = 0;
  const stack: string[] = [];
  const formatted = lines.map(line => {
    const trimmed = line.trim();
    let error = false;

    // Closing tag
    const closingTagMatch = trimmed.match(/^<\/([\w:-]+)>/);
    if (closingTagMatch) {
      const tagName = closingTagMatch[1];
      const last = stack.pop();
      if (last !== tagName) {
        error = true;
      }
      indent--;
    }

    const currentIndent = '|  '.repeat(Math.max(indent, 0));
    let outputLine = currentIndent + trimmed;

    // Opening tag (not closing, not self-closing)
    const openingTagMatch = trimmed.match(/^<([\w:-]+)(\s[^>]*)?>$/);
    const selfClosing = /\/>$/.test(trimmed);

    if (openingTagMatch && !selfClosing) {
      const tagName = openingTagMatch[1];
      stack.push(tagName);
      indent++;
    }

    if (error) {
      outputLine += ' // <------------------------- ERROR';
    }

    return outputLine;
  });

  return formatted.join('\n');
}

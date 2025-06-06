export function formatXML(xmlString) {
  try {
    const xmlDoc = new DOMParser().parseFromString(xmlString, "application/xml");

    // Check for parser errors
    if (xmlDoc.getElementsByTagName('parsererror').length) {
      throw new Error('Invalid XML');
    }

    // Format XML with indentation
    const formatted = xmlString.replace(/(>)(<)(\/*)/g, '$1\n$2$3')
                               .replace(/(<[^>]+>)/g, '\n$1')
                               .trim();
    return formatted;

  } catch (e) {
    return `Error: ${e.message}`;
  }
}
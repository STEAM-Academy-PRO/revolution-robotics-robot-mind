import aiBlocklyPrompt from "../views/utils/ai-blockly-prompt";

const typicalBlockNameFailures = {
  block_not: 'logic_not',
  block_if_then: 'if_then',
}

// save responses to a cache:
const cache = localStorage.getItem("aiResponses")
  ? JSON.parse(localStorage.getItem("aiResponses")!)
  : {};

const model = "gpt-4-turbo"; // Default model, can be changed if needed

export async function fetchAiResponse(
  prompt: string,
  options?: object,
  force: boolean = false
): Promise<{ xml: string; text: any }> {

  if (cache[prompt] && !force) {
    console.log("Using cached response for prompt:", prompt);
    return cache[prompt];
  }

  const response = await fetch("https://api.openai.com/v1/responses", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${import.meta.env.VITE_OPENAI_API_KEY}`,
    },
    body: JSON.stringify({
      model,
      input: prompt,
      text: { format: { type: "json_object" }},
      // Lower the temperature for more deterministic responses
      // Apparently if temp is 0 it will not be "creative" enough.
      // temperature: 0,
      ...options,
    }),
  });

  if (!response.ok) {
    throw new Error("Failed to fetch AI response");
  }

  const responseJson = await response.json();
  try {
    const jsonResponse = JSON.parse(responseJson.output[0].content[0].text);
    jsonResponse.xml = fixTypicalBlockNameFailures(jsonResponse.xml);
    cache[prompt] = jsonResponse;
    localStorage.setItem("aiResponses", JSON.stringify(cache));

    return jsonResponse;
  } catch (e) {
    console.error("Error parsing AI response:", e);
    console.error("Raw response:", responseJson);
    throw new Error("Invalid AI response format");
  }
}

export async function fetchAiXmlResponse(
  prompt: string,
  force: boolean = false
): Promise<{ xml?: string; text?: string; error?: string }> {
  return fetchAiResponse('JSON Response: ' + prompt, {instructions: aiBlocklyPrompt}, force);
}

export async function fixXmlError(
  originalQuery: string,
  xml: string,
  error: string
): Promise<string> {
  const response = await fetch("https://api.openai.com/v1/responses", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${import.meta.env.VITE_OPENAI_API_KEY}`,
    },
    body: JSON.stringify({
      model,
      input: xml,
      instructions: `Original query: "${originalQuery}"\n\n\nGot the following XML parsing error: ${error}\n\n\n Fix the XML formatting errors in the provided code. Return just the XML file this time, no JSON. Do not add any comments or explanations.`,
    }),
  });

  if (!response.ok) {
    throw new Error("Failed to fix XML error");
  }

  const responseJson = await response.json();

  // Save fixed XML to cache
  const fixedXml = fixTypicalBlockNameFailures(responseJson.output[0].content[0].text);
  cache[originalQuery] = {
    xml: fixedXml,
    text: responseJson.output[0].content[0].text,
  };

  return fixedXml;
}

export function fixTypicalBlockNameFailures(text: string): string {
  let result = text;
  for (const [key, value] of Object.entries(typicalBlockNameFailures)) {
    const regex = new RegExp(`\\b${key}\\b`, "g");
    result = result.replace(regex, value);
  }
  return result;
}

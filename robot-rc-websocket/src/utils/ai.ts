import aiBlocklyPrompt from "../views/utils/ai-blockly-prompt";

// save responses to a cache:
const cache = localStorage.getItem("aiResponses")
  ? JSON.parse(localStorage.getItem("aiResponses")!)
  : {};

const model = "gpt-3.5-turbo"; // Default model, can be changed if needed

export async function fetchAiResponse(
  prompt: string,
  options?: object
): Promise<{ xml: string; text: any }> {
  if (cache[prompt]) {
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
      // Lower the temperature for more deterministic responses
      temperature: 0,
      ...options,
    }),
  });

  if (!response.ok) {
    throw new Error("Failed to fetch AI response");
  }

  const responseJson = await response.json();

  const jsonResponse = JSON.parse(responseJson.output[0].content[0].text);

  cache[prompt] = jsonResponse;
  localStorage.setItem("aiResponses", JSON.stringify(cache));

  return jsonResponse;
}

export async function fetchAiXmlResponse(prompt: string): Promise<{ xml: string; text: any }> {
  return fetchAiResponse(prompt, {
    instructions: aiBlocklyPrompt,
  })
}


export async function fixXmlError(originalQuery: string, xml: string, error: string): Promise<string> {
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
      temperature: 0,
    }),
  });

  if (!response.ok) {
    throw new Error("Failed to fix XML error");
  }

  const responseJson = await response.json();

  // Save fixed XML to cache
  const fixedXml = responseJson.output[0].content[0].text;
  cache[originalQuery] = { xml: fixedXml, text: responseJson.output[0].content[0].text };

  return fixedXml;
}
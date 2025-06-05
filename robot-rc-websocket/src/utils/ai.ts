import aiBlocklyPrompt from "../views/utils/ai-blockly-prompt";

// save responses to a cache:
const cache = localStorage.getItem("aiResponses")
  ? JSON.parse(localStorage.getItem("aiResponses")!)
  : {};

export async function fetchAiResponse(prompt: string): Promise<{xml: string, text: any}> {
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
      model: "gpt-3.5-turbo",
      instructions: aiBlocklyPrompt,
      input: prompt,
    }),
  });

  if (!response.ok) {
    throw new Error("Failed to fetch AI response");
  }

  const responseJson = await response.json();

  const jsonResponse = JSON.parse(responseJson.output[0].content[0].text);

  cache[prompt] = jsonResponse;
  localStorage.setItem("aiResponses", JSON.stringify(cache));

  return jsonResponse
}

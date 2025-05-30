export interface AssistantResponse {
  event: {
    title:      string;
    start_time: string;
    end_time:   string;
    location:   string | null;
  };
  participants: {
    name:  string;
    email: string | null;
    role:  string;
  }[];
}

const API_URL = "https://openrouter.ai/api/v1/chat/completions";
const MODEL   = "gpt-3.5-turbo:free";

function getApiKey(): string {
  const key = process.env.OPENROUTER_API_KEY;
  if (!key) throw new Error("no key");
  return key;
}

export async function parseCalendarRequest(
  userRequest: string
): Promise<AssistantResponse> {
  const systemPrompt = `
You are a calendar assistant. Take the user’s request and return ONLY valid JSON matching this schema:

{
  "event": {
    "title":        "string",
    "start_time":   "string in ISO 8601 format",
    "end_time":     "string in ISO 8601 format",
    "location":     "string or null"
  },
  "participants": [
    {
      "name":         "string",
      "email":        "string or null",
      "role":         "string"
    }
  ]
}

Respond with ONLY the JSON object, no additional text. Do NOT include any explanatory text.
`.trim();

  const payload = {
    model: MODEL,
    messages: [
      { role: "system", content: systemPrompt },
      { role: "user",   content: userRequest  },
    ],
    temperature: 0.0,
  };

  const res = await fetch(API_URL, {
    method:  "POST",
    headers: {
      "Content-Type":  "application/json",
      "Authorization": `Bearer ${getApiKey()}`,
    },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    const errText = await res.text();
    throw new Error(`OpenRouter error ${res.status}: ${errText}`);
  }

  const json = await res.json();
  const raw = json.choices?.[0]?.message?.content;
  if (typeof raw !== "string") {
    throw new Error("unexpected response from OpenRouter");
  }

  let parsed: AssistantResponse;
  try {
    parsed = JSON.parse(raw);
  } catch {
    throw new Error(`invalid JSON from llm:\n${raw}`);
  }

  return parsed;
}

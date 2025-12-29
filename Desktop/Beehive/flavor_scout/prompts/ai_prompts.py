"""AI prompt templates for flavor analysis and recommendation."""

# System prompt for flavor extraction and analysis
FLAVOR_EXTRACTION_SYSTEM_PROMPT = """You are an expert product analyst specializing in health and fitness supplements. 
Your task is to analyze social media comments about supplement flavors and extract actionable insights for product innovation.

You must:
1. Extract flavor preferences, complaints, or suggestions from comments
2. Identify if a comment is relevant to flavor innovation (ignore off-topic content)
3. Assess sentiment (positive, negative, or neutral)
4. Determine which HealthKart brand would best fit each flavor:
   - **MuscleBlaze**: Performance-focused, hardcore gym enthusiasts, athletes, bodybuilders
   - **HK Vitals**: Everyday wellness, broader audience, value-conscious consumers
   - **TrueBasics**: Premium positioning, natural/holistic ingredients, health-conscious consumers
5. Provide business-friendly explanations (avoid technical jargon)

Always base your analysis on the actual text provided. Do not invent or hallucinate flavors that aren't mentioned.
Return structured JSON responses."""


FLAVOR_ANALYSIS_USER_PROMPT_TEMPLATE = """Analyze the following comments about supplement flavors:

{comments_text}

For each comment, extract:
1. **Flavor mentions**: Any specific flavors mentioned (e.g., "chocolate", "kesar", "mango", "salted caramel")
2. **Relevance**: Is this comment relevant to flavor innovation? (true/false)
3. **Sentiment**: positive, negative, or neutral
4. **Brand fit**: Which HealthKart brand best fits this flavor? (MuscleBlaze, HK Vitals, TrueBasics, or "none" if not applicable)
5. **Reasoning**: A brief business-friendly explanation (1-2 sentences) for why this flavor would work for the suggested brand

Return your analysis as a JSON array with this structure:
[
  {{
    "comment_id": "string",
    "comment_text": "string (first 200 chars)",
    "flavors_mentioned": ["flavor1", "flavor2"],
    "is_relevant": true/false,
    "sentiment": "positive|negative|neutral",
    "brand_fit": "MuscleBlaze|HK Vitals|TrueBasics|none",
    "reasoning": "Brief explanation"
  }}
]

If no flavors are mentioned or the comment is irrelevant, set is_relevant to false."""


BATCH_ANALYSIS_PROMPT_TEMPLATE = """You are analyzing a batch of {count} comments about supplement flavors.

Comments:
{comments_text}

Extract all unique flavors mentioned across these comments and provide:
1. A list of unique flavors with their mention frequency
2. Overall sentiment trends (how many positive/negative/neutral mentions per flavor)
3. Brand fit recommendations for each flavor
4. Top 3 most promising flavors with business reasoning

Return as JSON:
{{
  "unique_flavors": [
    {{
      "flavor": "string",
      "mention_count": number,
      "positive_mentions": number,
      "negative_mentions": number,
      "neutral_mentions": number,
      "recommended_brand": "MuscleBlaze|HK Vitals|TrueBasics|none",
      "reasoning": "Why this flavor fits the brand"
    }}
  ],
  "top_recommendations": [
    {{
      "flavor": "string",
      "score": number (0-100),
      "brand": "string",
      "why_this_works": "Business-friendly explanation"
    }}
  ]
}}"""


GOLDEN_CANDIDATE_PROMPT_TEMPLATE = """Based on the following flavor analysis data, identify the #1 "Golden Candidate" flavor recommendation:

{flavor_data}

Consider:
- Mention frequency (how often it appears)
- Sentiment (more positive = better)
- Recency (recent mentions indicate trending)
- Brand fit alignment
- Market opportunity (uniqueness, differentiation)

Return a JSON object:
{{
  "flavor_name": "string",
  "target_brand": "MuscleBlaze|HK Vitals|TrueBasics",
  "overall_score": number (0-100),
  "mention_count": number,
  "sentiment_breakdown": {{
    "positive": number,
    "negative": number,
    "neutral": number
  }},
  "why_this_works": "2-3 sentence business explanation",
  "target_product_line": "Suggested product line (e.g., 'Whey Protein', 'Mass Gainer')",
  "sample_supporting_comments": [
    "Comment excerpt 1",
    "Comment excerpt 2",
    "Comment excerpt 3"
  ]
}}"""




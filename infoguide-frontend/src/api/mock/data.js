export const MOCK_INGESTION = {
  fileName: 'Q3_2024_Financial_Report.pdf',
  pages: 42,
  extractedImages: 8,
  extractedTables: 5,
  rawText: `ACME Corporation — Q3 2024 Financial Report

Executive Summary

ACME Corporation delivered strong financial performance in the third quarter of 2024, with total revenue reaching $2.8 billion, representing a 15.3% increase year-over-year. Operating income improved to $487 million, while net income rose to $312 million, driven by operational efficiency initiatives and robust demand across core business segments.

Revenue Analysis

Product revenue accounted for $1.92 billion (68.6% of total revenue), growing 18.2% compared to Q3 2023. Services revenue contributed $880 million (31.4%), growing 10.1% year-over-year. The growth was primarily driven by three factors: expansion into Asia-Pacific markets, introduction of the Enterprise Suite product line, and improved customer retention rates reaching 94.2%.

The Asia-Pacific segment showed the most significant acceleration, growing 34.1% year-over-year and contributing $420 million in total revenue. North America remained the largest market at $1.6 billion, growing at 11.2%, while EMEA contributed $780 million with 13.8% growth.

Operating Expenses

Total operating expenses for Q3 2024 were $2.31 billion, up 11.4% from Q3 2023. Research and development spending increased to $340 million (12.1% of revenue), reflecting continued investment in next-generation product development. Sales and marketing expenses were $580 million (20.7% of revenue). General and administrative expenses decreased to $210 million due to workforce optimization measures implemented in Q2 2024.

Risk Factors

Key risks include macroeconomic uncertainty affecting enterprise IT spending, intensifying competition in cloud services, and potential supply chain disruptions. Currency headwinds impacted international revenue by approximately $45 million. The company maintains a conservative balance sheet with $1.2 billion in cash and equivalents.

Liquidity and Capital Resources

Cash and cash equivalents at quarter-end totaled $1.2 billion, up from $950 million at the end of Q2 2024. Free cash flow for the quarter was $298 million. The company repurchased $150 million of common stock during the quarter.

Outlook

For Q4 2024, ACME expects revenue in the range of $2.9 billion to $3.0 billion, representing 12–16% growth. Full-year 2024 revenue guidance is raised to $11.0–$11.2 billion. Operating margin is expected to expand by 50–75 basis points compared to full-year 2023.`,
}

export const MOCK_PREPROCESSING = {
  stats: {
    removedInvisibleChars: 847,
    fixedHyphenations: 12,
    removedHeaders: 3,
    removedFooters: 3,
    normalizedSpaces: 234,
  },
  cleanedText: `ACME Corporation — Q3 2024 Financial Report

Executive Summary

ACME Corporation delivered strong financial performance in the third quarter of 2024, with total revenue reaching $2.8 billion, representing a 15.3% increase year-over-year. Operating income improved to $487 million, while net income rose to $312 million, driven by operational efficiency initiatives and robust demand across core business segments.

Revenue Analysis

Product revenue accounted for $1.92 billion (68.6% of total revenue), growing 18.2% compared to Q3 2023. Services revenue contributed $880 million (31.4%), growing 10.1% year-over-year. The growth was primarily driven by three factors: expansion into Asia-Pacific markets, introduction of the Enterprise Suite product line, and improved customer retention rates reaching 94.2%.

The Asia-Pacific segment showed the most significant acceleration, growing 34.1% year-over-year and contributing $420 million in total revenue. North America remained the largest market at $1.6 billion, growing at 11.2%, while EMEA contributed $780 million with 13.8% growth.

Operating Expenses

Total operating expenses for Q3 2024 were $2.31 billion, up 11.4% from Q3 2023. Research and development spending increased to $340 million (12.1% of revenue), reflecting continued investment in next-generation product development.

Risk Factors

Key risks include macroeconomic uncertainty affecting enterprise IT spending, intensifying competition in cloud services, and potential supply chain disruptions. Currency headwinds impacted international revenue by approximately $45 million.

Outlook

For Q4 2024, ACME expects revenue in the range of $2.9 billion to $3.0 billion, representing 12–16% growth. Full-year 2024 revenue guidance is raised to $11.0–$11.2 billion.`,
}

export const MOCK_CHUNKS = {
  totalChunks: 8,
  chunks: [
    {
      id: 'chunk_0',
      heading: 'Executive Summary',
      text: 'ACME Corporation delivered strong financial performance in the third quarter of 2024, with total revenue reaching $2.8 billion, representing a 15.3% increase year-over-year. Operating income improved to $487 million, while net income rose to $312 million, driven by operational efficiency initiatives and robust demand across core business segments.',
      metadata: { sectionIndex: 0, charCount: 347, pageNumbers: [1, 2] },
    },
    {
      id: 'chunk_1',
      heading: 'Revenue Analysis',
      text: 'Product revenue accounted for $1.92 billion (68.6% of total revenue), growing 18.2% compared to Q3 2023. Services revenue contributed $880 million (31.4%), growing 10.1% year-over-year. The growth was primarily driven by three factors: expansion into Asia-Pacific markets, introduction of the Enterprise Suite product line, and improved customer retention rates reaching 94.2%.',
      metadata: { sectionIndex: 1, charCount: 362, pageNumbers: [3, 4] },
    },
    {
      id: 'chunk_2',
      heading: 'Revenue Analysis — Regional Breakdown',
      text: 'The Asia-Pacific segment showed the most significant acceleration, growing 34.1% year-over-year and contributing $420 million in total revenue. North America remained the largest market at $1.6 billion, growing at 11.2%, while EMEA contributed $780 million with 13.8% growth.',
      metadata: { sectionIndex: 1, charCount: 280, pageNumbers: [4, 5] },
    },
    {
      id: 'chunk_3',
      heading: 'Operating Expenses',
      text: 'Total operating expenses for Q3 2024 were $2.31 billion, up 11.4% from Q3 2023. Research and development spending increased to $340 million (12.1% of revenue), reflecting continued investment in next-generation product development. Sales and marketing expenses were $580 million (20.7% of revenue). General and administrative expenses decreased to $210 million due to workforce optimization measures implemented in Q2 2024.',
      metadata: { sectionIndex: 2, charCount: 408, pageNumbers: [6, 7] },
    },
    {
      id: 'chunk_4',
      heading: 'Risk Factors',
      text: 'Key risks include macroeconomic uncertainty affecting enterprise IT spending, intensifying competition in cloud services, and potential supply chain disruptions. Currency headwinds impacted international revenue by approximately $45 million. The company maintains a conservative balance sheet with $1.2 billion in cash and equivalents.',
      metadata: { sectionIndex: 3, charCount: 324, pageNumbers: [18, 19] },
    },
    {
      id: 'chunk_5',
      heading: 'Liquidity and Capital Resources',
      text: 'Cash and cash equivalents at quarter-end totaled $1.2 billion, up from $950 million at the end of Q2 2024. Free cash flow for the quarter was $298 million. The company repurchased $150 million of common stock during the quarter.',
      metadata: { sectionIndex: 4, charCount: 232, pageNumbers: [22, 23] },
    },
    {
      id: 'chunk_6',
      heading: 'Outlook',
      text: 'For Q4 2024, ACME expects revenue in the range of $2.9 billion to $3.0 billion, representing 12–16% growth. Full-year 2024 revenue guidance is raised to $11.0–$11.2 billion. Operating margin is expected to expand by 50–75 basis points compared to full-year 2023.',
      metadata: { sectionIndex: 5, charCount: 261, pageNumbers: [38, 39] },
    },
    {
      id: 'chunk_7',
      heading: 'Executive Summary — Financial Highlights',
      text: 'Key financial metrics for Q3 2024: Revenue $2.8B (+15.3% YoY), Gross Margin 58.4% (+120 bps), Operating Income $487M (+22.1%), Net Income $312M (+19.8%), EPS $1.84 (+21.1%), Free Cash Flow $298M. The company achieved its seventh consecutive quarter of double-digit revenue growth.',
      metadata: { sectionIndex: 0, charCount: 290, pageNumbers: [2] },
    },
  ],
}

export const MOCK_EMBEDDING = {
  model: 'BAAI/bge-m3',
  dimension: 1024,
  totalChunks: 8,
  processingTimeSeconds: 12.4,
  normalizedVectors: true,
}

export const MOCK_IMAGE_DESCRIPTION = {
  processed: 3,
  skipped: 5,
  newTotalChunks: 11,
  imageChunks: [
    {
      id: 'img_chunk_0',
      imageFile: 'figure_1_revenue_chart.png',
      heading: 'Image Description: Revenue Growth Chart',
      text: 'Bar chart comparing quarterly revenue from Q1 2023 through Q3 2024. Blue bars represent product revenue; orange bars represent services revenue. A dashed trend line shows consistent upward trajectory. Q3 2024 shows the highest values with product revenue at $1.92B and services at $880M. Y-axis ranges from $0 to $3.0B.',
      metadata: { type: 'image_description', pageNumber: 8, dimensions: '1024x768' },
    },
    {
      id: 'img_chunk_1',
      imageFile: 'figure_2_regional_breakdown.png',
      heading: 'Image Description: Regional Revenue Pie Chart',
      text: 'Pie chart showing revenue distribution by geographic region in Q3 2024. North America 57.1% ($1.6B), EMEA 27.9% ($780M), Asia-Pacific 15.0% ($420M). A small callout box highlights Asia-Pacific as the fastest growing region at +34.1% YoY. The chart uses a professional color scheme of dark blue, medium blue, and light blue.',
      metadata: { type: 'image_description', pageNumber: 12, dimensions: '800x600' },
    },
    {
      id: 'img_chunk_2',
      imageFile: 'figure_3_margin_waterfall.png',
      heading: 'Image Description: Operating Margin Waterfall Chart',
      text: 'Waterfall chart illustrating the components of operating margin improvement from Q3 2023 (16.2%) to Q3 2024 (17.4%). Positive contributors in green: R&D efficiency (+0.8%), G&A optimization (+0.6%), product mix shift (+0.4%). Negative factors in red: increased S&M spend (-0.4%), FX headwinds (-0.2%). Net improvement of +1.2 percentage points.',
      metadata: { type: 'image_description', pageNumber: 21, dimensions: '1200x500' },
    },
  ],
}

export const MOCK_QUERY_EXPANSION = {
  intent: 'Identify the primary business factors, strategic initiatives, and market dynamics that contributed to revenue increase in Q3 2024',
  keywords: [
    'revenue growth', 'Q3 2024', 'growth drivers', 'business segments',
    'product revenue', 'services revenue', 'Asia-Pacific expansion',
    'Enterprise Suite', 'customer retention', 'market growth',
  ],
  expandedQuery: 'What were the primary factors, strategic initiatives, and business drivers contributing to revenue growth and increase in the third quarter of fiscal year 2024, including product and services performance, geographic expansion, and new product lines?',
}

export const MOCK_RETRIEVAL = {
  method: 'hybrid',
  topK: 5,
  results: [
    {
      rank: 1,
      chunkId: 'chunk_1',
      heading: 'Revenue Analysis',
      text: 'Product revenue accounted for $1.92 billion (68.6% of total revenue), growing 18.2% compared to Q3 2023. Services revenue contributed $880 million (31.4%), growing 10.1% year-over-year. The growth was primarily driven by three factors: expansion into Asia-Pacific markets, introduction of the Enterprise Suite product line, and improved customer retention rates reaching 94.2%.',
      score: 0.912,
      faissRank: 1,
      bm25Rank: 2,
    },
    {
      rank: 2,
      chunkId: 'chunk_2',
      heading: 'Revenue Analysis — Regional Breakdown',
      text: 'The Asia-Pacific segment showed the most significant acceleration, growing 34.1% year-over-year and contributing $420 million in total revenue. North America remained the largest market at $1.6 billion, growing at 11.2%, while EMEA contributed $780 million with 13.8% growth.',
      score: 0.874,
      faissRank: 2,
      bm25Rank: 3,
    },
    {
      rank: 3,
      chunkId: 'chunk_0',
      heading: 'Executive Summary',
      text: 'ACME Corporation delivered strong financial performance in the third quarter of 2024, with total revenue reaching $2.8 billion, representing a 15.3% increase year-over-year. Operating income improved to $487 million, while net income rose to $312 million, driven by operational efficiency initiatives and robust demand across core business segments.',
      score: 0.821,
      faissRank: 3,
      bm25Rank: 1,
    },
    {
      rank: 4,
      chunkId: 'img_chunk_0',
      heading: 'Image Description: Revenue Growth Chart',
      text: 'Bar chart comparing quarterly revenue from Q1 2023 through Q3 2024. Blue bars represent product revenue; orange bars represent services revenue. A dashed trend line shows consistent upward trajectory. Q3 2024 shows the highest values with product revenue at $1.92B and services at $880M.',
      score: 0.756,
      faissRank: 4,
      bm25Rank: 6,
    },
    {
      rank: 5,
      chunkId: 'chunk_6',
      heading: 'Outlook',
      text: 'For Q4 2024, ACME expects revenue in the range of $2.9 billion to $3.0 billion, representing 12–16% growth. Full-year 2024 revenue guidance is raised to $11.0–$11.2 billion. Operating margin is expected to expand by 50–75 basis points compared to full-year 2023.',
      score: 0.698,
      faissRank: 6,
      bm25Rank: 4,
    },
  ],
}

export const MOCK_RERANKING = {
  topK: 3,
  results: [
    {
      newRank: 1,
      originalRank: 1,
      chunkId: 'chunk_1',
      heading: 'Revenue Analysis',
      text: 'Product revenue accounted for $1.92 billion (68.6% of total revenue), growing 18.2% compared to Q3 2023. Services revenue contributed $880 million (31.4%), growing 10.1% year-over-year. The growth was primarily driven by three factors: expansion into Asia-Pacific markets, introduction of the Enterprise Suite product line, and improved customer retention rates reaching 94.2%.',
      rerankScore: 8.73,
      originalScore: 0.912,
    },
    {
      newRank: 2,
      originalRank: 3,
      chunkId: 'chunk_0',
      heading: 'Executive Summary',
      text: 'ACME Corporation delivered strong financial performance in the third quarter of 2024, with total revenue reaching $2.8 billion, representing a 15.3% increase year-over-year. Operating income improved to $487 million, while net income rose to $312 million, driven by operational efficiency initiatives and robust demand across core business segments.',
      rerankScore: 8.41,
      originalScore: 0.821,
    },
    {
      newRank: 3,
      originalRank: 2,
      chunkId: 'chunk_2',
      heading: 'Revenue Analysis — Regional Breakdown',
      text: 'The Asia-Pacific segment showed the most significant acceleration, growing 34.1% year-over-year and contributing $420 million in total revenue. North America remained the largest market at $1.6 billion, growing at 11.2%, while EMEA contributed $780 million with 13.8% growth.',
      rerankScore: 7.92,
      originalScore: 0.874,
    },
  ],
}

export const MOCK_GENERATION = {
  model: 'gpt-4o-mini',
  answer: `Based on the Q3 2024 Financial Report, the main drivers of revenue growth were:

**1. Asia-Pacific Market Expansion**
The Asia-Pacific segment was the fastest-growing region, expanding 34.1% year-over-year and contributing $420 million in total revenue. This geographic expansion was explicitly cited as one of the three primary growth drivers.

**2. Enterprise Suite Product Launch**
The introduction of the Enterprise Suite product line drove product revenue growth of 18.2% year-over-year, with total product revenue reaching $1.92 billion (68.6% of total revenue).

**3. Improved Customer Retention**
Customer retention rates improved to 94.2%, increasing recurring revenue from the existing customer base and reducing churn-related revenue leakage.

Overall, total revenue reached $2.8 billion, a 15.3% increase year-over-year. Services revenue also contributed, growing 10.1% to $880 million. The company achieved its seventh consecutive quarter of double-digit revenue growth.`,
  citedChunks: [
    { chunkId: 'chunk_1', heading: 'Revenue Analysis' },
    { chunkId: 'chunk_0', heading: 'Executive Summary' },
    { chunkId: 'chunk_2', heading: 'Revenue Analysis — Regional Breakdown' },
  ],
  inputTokens: 2840,
  outputTokens: 213,
}

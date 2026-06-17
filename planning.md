# FitFindr — planning.md

> Complete this document before writing any implementation code.
> Your spec and agent diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Your planning.md will be reviewed as part of your submission.
> Update it before starting any stretch features.

---

## Tools

List every tool your agent will use. For each tool, fill in all four fields.
You must have at least 3 tools. The three required tools are listed — add any additional tools below them.

### Tool 1: search_listings

**What it does:**
<!-- Describe what this tool does in 1–2 sentences -->
The tools takes desired clothing item, size of the clothing and the max price. It then returns matching listings sorted by relevance.

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `description` (str): desired clothing item 
- `size` (str): the size of the clothing
- `max_price` (float): the max price

**What it returns:**
<!-- Describe the return value — what fields does a result contain? -->
List of matching listing dicts sorted by relevance.

**What happens if it fails or returns nothing:**
<!-- What should the agent do if no listings match? -->
Agent returns message asking user to try differently and stops executing.
---

### Tool 2: suggest_outfit

**What it does:**
<!-- Describe what this tool does in 1–2 sentences -->
Takes the listed item and users wardrobe. Then it pairs it with existing clothing as a suggestion

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `new_item` (dict): list of all the listings from previous agent. key -> id, value -> entire listing.
- `wardrobe` (dict): key -> id, value -> entire wardrobe object

**What it returns:**
<!-- Describe the return value -->
Suggestions for the outfit, basically top and bottom fit. (str)

**What happens if it fails or returns nothing:**
<!-- What should the agent do if the wardrobe is empty or no outfit can be suggested? -->
Return an empty suggestion.

---

### Tool 3: create_fit_card

**What it does:**
<!-- Describe what this tool does in 1–2 sentences -->
Generated a short shareable decription for the outfit.

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `outfit` (...): suggested oufit frim suggest_outfit agent.

**What it returns:**
<!-- Describe the return value -->
(Str) -> short shareable decription for the outfit.

**What happens if it fails or returns nothing:**
<!-- What should the agent do if the outfit data is incomplete? -->
Return a generic outfit suggestion
---

### Additional Tools (if any)

<!-- Copy the block above for any tools beyond the required three -->

---

## Planning Loop

**How does your agent decide which tool to call next?**
<!-- Describe the logic your planning loop uses. What does it look at? What conditions change its behavior? How does it know when it's done? -->
The agent decides the tool to be called based on the input passed by the user and data available from the previous tool.
Start by checking the user’s query for a shopping request:

If the user asks for new clothing or a specific item, call search_listings first.
If the user only wants styling advice for existing wardrobe items, skip directly to suggest_outfit.
After search_listings returns:

If it returns matching listings, save those results and call suggest_outfit using the new listings plus the user wardrobe.
If it returns no results, stop and return a polite message asking the user to try a different description, size, or price.
After suggest_outfit returns:

If an outfit suggestion is produced, call create_fit_card to generate a short shareable description.
If it fails or cannot suggest an outfit, return a fallback message explaining that styling suggestions are unavailable.
When create_fit_card returns:

Present the final composed response to the user.
The loop is done once the final card or fallback message is ready.

The loop is complete when the agent has either:

produced a final outfit + listing recommendation, or
handled a failure case with a user-facing response.

---

## State Management

**How does information from one tool get passed to the next?**
<!-- Describe how your agent stores and accesses state within a session. What data is tracked? How is it passed between tool calls? -->
We use a session state object to track the current request and intermediate results.
---

## Error Handling

For each tool, describe the specific failure mode you're handling and what the agent does in response.

| Tool | Failure mode | Agent response |
|------|-------------|----------------|
| search_listings | No results match the query | |
| suggest_outfit | Wardrobe is empty | |
| create_fit_card | Outfit input is missing or incomplete | |

| Tool | Failure mode | Agent response |
|------|-------------|----------------|
| search_listings |	No results match the query |	Return a polite message asking the user to rephrase their request, broaden the description, change size, or raise the max price; stop the tool chain. |
| suggest_outfit |	Wardrobe is empty	Return an empty outfit suggestion and a friendly note that styling advice is unavailable without wardrobe items; still surface the search results if available. |
| create_fit_card |	Outfit input is missing or incomplete	Return a generic outfit card message such as “Here’s a versatile look to try,” and include the available item details rather than failing outright. |

---

## Architecture

<!-- Draw a diagram of your agent showing how the components connect:
     User input → Planning Loop → Tools (search_listings, suggest_outfit, create_fit_card)
                                                                          ↕
                                                                   State / Session
     Show what triggers each tool, how state flows between them, and where error paths branch off.
     ASCII art, a Mermaid diagram (https://mermaid.js.org/syntax/flowchart.html), or an embedded
     sketch are all fine. You'll share this diagram with an AI tool when asking it to implement
     the planning loop and each individual tool. -->
User Input (query + wardrobe_choice) │ ▼ Parse Query • Extract: description, size, max_price • Load wardrobe │ ▼ Session State ◀─ Store parsed params │ ▼ search_listings(description, size, max_price) INPUT: description, size, max_price OUTPUT: list of matching items │ ├─ NO RESULTS ─────────┐ │ │ │ ▼ │ ❌ Set session["error"] │ Return Early │ ├─ HAS RESULTS │ ▼ Session State ◀─ Store search_results, selected_item │ ▼ suggest_outfit(new_item, wardrobe) INPUT: selected_item, wardrobe OUTPUT: outfit suggestion string │ ▼ Session State ◀─ Store outfit_suggestion │ ▼ create_fit_card(outfit, new_item) INPUT: outfit_suggestion, selected_item OUTPUT: fit card caption string │ ▼ Session State ◀─ Store fit_card │ ▼ price_comparison(new_item, listings) INPUT: selected_item, all listings OUTPUT: price assessment string │ ▼ Session State ◀─ Store price_assessment │ ▼ Return Complete Session Dict to User │ ▼ Display: Listing + Outfit + Caption + Price

---

## AI Tool Plan

<!-- For each part of the implementation below, describe:
     - Which AI tool you plan to use (Claude, Copilot, ChatGPT, etc.)
     - What you'll give it as input (which sections of this planning.md, your agent diagram)
     - What you expect it to produce
     - How you'll verify the output matches your spec before moving on

     "I'll use AI to help me code" is not a plan.
     "I'll give Claude my Tool 1 spec (inputs, return value, failure mode) and ask it to implement
     search_listings() using load_listings() from the data loader — then test it against 3 queries
     before trusting it" is a plan. -->

**Milestone 3 — Individual tool implementations:**
I’ll ask Claude to implement each tool using the exact inputs, return values, and failure modes defined in planning.md:

For search_listings, I’ll provide Tool 1’s spec and have Claude implement search_listings() using load_listings() from the data loader.
For suggest_outfit, I’ll provide Tool 2’s spec and have Claude implement suggest_outfit() using the Groq API with new_item and wardrobe.
For create_fit_card, I’ll provide Tool 3’s spec and have Claude implement create_fit_card() using the Groq API with outfit and new_item.

**Milestone 4 — Planning loop and state management:**
I’ll ask Claude to implement each tool according to the exact specs in planning.md:

For search_listings, give Claude Tool 1’s inputs, return shape, and failure behavior, and have it implement search_listings() using load_listings() from the data loader.
For suggest_outfit, give Claude Tool 2’s inputs, return shape, and failure behavior, and have it implement suggest_outfit() using the Groq API with new_item and wardrobe.
For create_fit_card, give Claude Tool 3’s inputs, return shape, and failure behavior, and have it implement create_fit_card() using the Groq API with outfit and new_item.
I’ll structure agent.py with a fixed processing flow:

Initialize a session dictionary.
Parse the user query into description, size, and max_price.
Call search_listings.
If no results are returned, set session["error"] and return early.
If results exist, save search_results and selected_item in session.
Call suggest_outfit with selected_item and wardrobe, then store outfit_suggestion in session.
Call create_fit_card with outfit_suggestion and selected_item, then store fit_card in session.
Call price_comparison with selected_item and all listings, then store price_assessment in session.
Return the completed session dictionary with all results.
---

## A Complete Interaction (Step by Step)

Write out what a full user interaction looks like from start to finish — tool call by tool call. Use a specific example query.

**Example user query:** "I'm looking for a vintage graphic tee under $30. I mostly wear baggy jeans and chunky sneakers. What's out there and how would I style it?"

**Step 1:**
<!-- What does the agent do first? Which tool is called? With what input? -->
Agent parses the query into:
description: "vintage graphic tee"
size: inferred or asked from user if missing (e.g. "M")
max_price: 30.0
Agent calls search_listings(description, size, max_price)

**Step 2:**
<!-- What happens next? What was returned from step 1? What tool is called now? -->
search_listings returns matching listing results sorted by relevance
Agent stores:
session["search_results"]
session["selected_item"] (top match)
Agent calls suggest_outfit(new_item=selected_item, wardrobe=user_wardrobe)

**Step 3:**
<!-- Continue until the full interaction is complete -->
suggest_outfit returns a styling suggestion using the new tee and existing wardrobe pieces
Agent stores:
session["outfit_suggestion"]
Agent calls create_fit_card(outfit=outfit_suggestion, new_item=selected_item)

**Final output to user:**
<!-- What does the user actually see at the end? -->
A composed response containing:
the best matching vintage graphic tee listing(s)
a suggested outfit pairing using the user’s wardrobe
a short shareable fit card description
any price assessment or recommendation notes
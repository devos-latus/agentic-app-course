# Multi-Agent CSV Analytics System 🚀

A sophisticated CSV analysis system powered by specialized AI agents, featuring deterministic workflows, intelligent guardrails, and comprehensive memory management. Built following agentic_app_quickstart patterns with robust error handling and extensive testing.

## ⚠️ **Current Implementation Status**

- ✅ **Terminal Interface** (`main.py`) - **FULLY WORKING** - Complete implementation with all features
- 🚧 **Web Interface** (`gradio_app.py`) - **IN DEVELOPMENT** - Will be implemented in future phases
- ✅ **Chat Service Layer** (`chat_service.py`) - **FULLY WORKING** - Shared business logic ready for both interfaces

## 🏗️ System Architecture

### Core Components
```
week_1/solution/
├── main.py              # Terminal CLI application
├── gradio_app.py        # Modern web interface with multi-user support
├── chat_service.py      # Shared service layer for both interfaces
├── csv_agents.py        # All agents with handoff relationships & guardrails
├── tools.py             # Function tools for data operations
├── visualization_core.py # Chart generation and visualization tools
├── charts/              # Generated chart files (auto-cleaned after sessions)
└── data/                # Sample CSV files (auto-loaded at startup)
    ├── employee_data.csv
    ├── sample_sales.csv
    └── weather_data.csv
```

## 🤖 Agent Architecture & Deterministic Flow

### Actual Agent Flows

The system has **multiple distinct flows** depending on the request type:

#### **Flow 1: Simple Analytics** (Average, Count, etc.)
```
User → Communication Agent → Analytics Agent → Communication Agent → User
                                    ↓
                            Uses simple tools directly
                            (calculate_column_average, etc.)
```

#### **Flow 2: Complex SQL Analysis** (Median, Complex Queries)
```
User → Communication Agent → Analytics Agent → Query Planner → SQL Writer → Query Evaluator → Communication Agent → User
                                    ↓              ↓              ↓              ↓
                              Recognizes      Creates SQL     Executes      Validates
                              complexity      plan           query         results
```

#### **Flow 3: Visualization Requests**
```
User → Communication Agent → Analytics Agent → Visualization Agent → Communication Agent → User
                                    ↓                    ↓
                              Gets data with         Creates PNG
                              execute_sql_query()    chart file
```

#### **Flow 4: Data Loading**
```
User → Communication Agent → Data Loader Agent → Communication Agent → User
                                    ↓
                              Loads CSV files
                              into SQLite
```

### Key Architectural Insights

#### **Communication Agent as Hub**
- **Always starts and ends** with Communication Agent
- **No direct agent-to-agent transfers** - everything flows through Communication
- **Consistent user experience** regardless of which specialists are involved

#### **Deterministic SQL Chain** (Flow 2)
- **Linear progression**: Query Planner → SQL Writer → Query Evaluator
- **No loops back to Analytics**: Query Evaluator goes directly to Communication Agent
- **Separation of concerns**: Each agent has one specific job in the chain

#### **Visualization Isolation** (Flow 3)
- **Only Analytics Agent** can decide to create visualizations
- **Separate from SQL chain**: Visualization Agent is not part of the deterministic SQL flow
- **Direct return**: Visualization Agent returns directly to Communication Agent

#### **Smart Routing**
- **Analytics Agent decides**: Simple tools vs complex SQL vs visualization
- **Request type determines flow**: System automatically routes based on question complexity
- **No user awareness needed**: Users don't need to know which flow their question will take

### Why Deterministic Agent Flow?

The system uses a **deterministic agent flow** rather than free-form agent communication for several critical reasons:

1. **Predictable Query Processing**: Complex data analysis requires systematic planning, execution, and validation
2. **Quality Assurance**: Each query goes through validation and sanity checking before reaching the user
3. **Error Recovery**: Failed queries can be systematically debugged and retried through the pipeline
4. **Expertise Specialization**: Each agent focuses on one specific task (planning, writing SQL, validation)
5. **Consistent Results**: Users get reliable, validated answers rather than potentially incorrect free-form responses

### Agent Handoff Configuration

The flows above are implemented using this handoff configuration:

```python
# Agent handoff relationships
communication_agent.handoffs = [analytics_agent, data_loader_agent]
analytics_agent.handoffs = [communication_agent, query_planner_agent, visualization_agent]
query_planner_agent.handoffs = [sql_writer_agent]
sql_writer_agent.handoffs = [query_evaluator_agent]
query_evaluator_agent.handoffs = [communication_agent, query_planner_agent, sql_writer_agent]
data_loader_agent.handoffs = [communication_agent]
visualization_agent.handoffs = [communication_agent]
```

**Key Points:**
- **Communication Agent** is the hub - all flows start and end there
- **Analytics Agent** is the decision maker - routes to SQL chain or visualization
- **SQL Chain** is linear and deterministic: Planner → Writer → Evaluator
- **Query Evaluator** returns directly to Communication (bypasses Analytics)
- **Visualization Agent** only accessible via Analytics Agent
```

## 🛡️ Guardrails & Safety

#### Detailed Agent Responsibilities

**1. Communication Agent** (`communication_agent`)
- **Role**: User interface and response formatting
- **Tools**: `get_all_tables`, `get_table_schema`
- **Handoffs**: `[analytics_agent, data_loader_agent]`
- **Purpose**: Welcomes users, formats technical results into friendly language

**2. Analytics Agent** (`analytics_agent`) 
- **Role**: Determines query complexity and routes appropriately
- **Tools**: `calculate_column_average`, `count_rows_with_value`, `get_table_schema`, `get_all_tables`
- **Handoffs**: `[communication_agent, query_planner_agent]`
- **Decision Logic**: 
  - Simple queries → Direct function tools
  - Complex queries → SQL pipeline via Query Planner

**3. Query Planner Agent** (`query_planner_agent`)
- **Role**: Plans complex SQL queries systematically
- **Tools**: `get_table_schema`, `get_all_tables`, `get_column_names`
- **Handoffs**: `[sql_writer_agent]`
- **Output**: Structured `QueryPlan` with tables, columns, operations needed

**4. SQL Writer Agent** (`sql_writer_agent`)
- **Role**: Generates optimized SQL from plans
- **Tools**: `get_table_schema`, `get_all_tables`
- **Handoffs**: `[query_evaluator_agent]`
- **Focus**: Efficient, safe SQL generation (SELECT only)

**5. Query Evaluator Agent** (`query_evaluator_agent`)
- **Role**: Validates results and performs sanity checks
- **Tools**: `execute_sql_query`, `execute_sql_analysis`, `get_table_schema`
- **Handoffs**: `[communication_agent, query_planner_agent, sql_writer_agent]`
- **Validation**: Runs additional queries to verify results, checks data ranges

**6. Data Loader Agent** (`data_loader_agent`)
- **Role**: Handles file loading and data discovery
- **Tools**: `load_csv_file`, `discover_and_load_csv_files`, `get_all_tables`
- **Handoffs**: `[communication_agent]`
- **Purpose**: Startup data loading, new file processing

## 🛡️ Intelligent Guardrails

### Input Guardrails
```python
@input_guardrail
async def analytics_input_guardrail(input: str, ctx: RunContextWrapper) -> GuardrailFunctionOutput:
    """Ensures user questions are analytics-related using AnalyticsTopicCheck model"""
```

**Purpose**: Filters out non-analytics questions (weather, recipes, etc.)
**Model**: `AnalyticsTopicCheck` with `is_analytics_related` boolean and reasoning
**Action**: Blocks off-topic questions with helpful redirection messages

### Output Guardrails  
```python
@output_guardrail
async def analytics_output_guardrail(output: str, ctx: RunContextWrapper) -> GuardrailFunctionOutput:
    """Ensures agent responses stay focused on analytics topics using ResponseTopicCheck model"""
```

**Purpose**: Prevents agents from discussing non-analytics topics in responses
**Model**: `ResponseTopicCheck` with `is_on_topic` boolean and reasoning
**Action**: Filters responses that drift from data analysis topics

### Guardrail Integration
- **Communication Agent**: Protected by both input and output guardrails
- **Error Handling**: `InputGuardrailTripwireTriggered` and `OutputGuardrailTripwireTriggered` exceptions
- **User Experience**: Helpful messages when guardrails trigger instead of generic errors

## 🔧 Function Tools & Data Operations

### Data Loading & Discovery
```python
@function_tool
def discover_and_load_csv_files(data_directory: str) -> Dict[str, Any]
# Auto-discovers and loads all CSV files from directory at startup

@function_tool  
def load_csv_file(file_path: str, table_name: str) -> Dict[str, Any]
# Loads individual CSV files with automatic data type detection
```

### Schema & Metadata Tools
```python
@function_tool
def get_all_tables() -> Dict[str, Any]
# Returns all loaded tables with row counts and column information

@function_tool
def get_table_schema(table_name: str) -> Dict[str, Any] 
# Detailed schema with column names, types, and sample data

@function_tool
def get_column_names(table_name: str) -> Dict[str, Any]
# Quick column name lookup for query planning
```

### Statistical Analysis Tools
```python
@function_tool
def calculate_column_average(table_name: str, column_name: str) -> Dict[str, Any]
# Calculates mean values with error handling for non-numeric data

@function_tool
def count_rows_with_value(table_name: str, column_name: str, value: str) -> Dict[str, Any]
# Counts occurrences with flexible string matching
```

### SQL Execution Tools
```python
@function_tool  
def execute_sql_query(sql_query: str) -> Dict[str, Any]
# Safe SQL execution (SELECT only) with comprehensive error handling

@function_tool
def execute_sql_analysis(description: str, sql_query: str) -> Dict[str, Any]
# Enhanced SQL execution with analysis context and result interpretation
```

## 💾 Data Initialization & SQLite Integration

### Automatic Startup Process
1. **Directory Scan**: `discover_and_load_csv_files("data")` scans for CSV files
2. **Type Detection**: Pandas automatically infers data types during CSV reading
3. **SQLite Conversion**: DataFrames converted to SQLite tables with `df.to_sql()`
4. **Schema Extraction**: `PRAGMA table_info()` captures column metadata
5. **Memory Storage**: In-memory SQLite database (`:memory:`) for fast queries
6. **User Welcome**: Communication Agent provides data overview to users

### SQLite Design Decisions
- **In-Memory Database**: Fast queries, no persistence between sessions
- **Pandas Integration**: Automatic type inference and conversion
- **Thread Safety**: `check_same_thread=False` for multi-user support
- **Foreign Keys**: `PRAGMA foreign_keys = ON` for data integrity
- **SELECT-Only**: Safety constraint prevents data modification

## 🧠 Memory Management & Session Handling

### Session Architecture
```python
# Multi-user support with unique sessions
session = SQLiteSession(session_id=str(uuid.uuid4()))

# Terminal: Simple session ID  
session = SQLiteSession(session_id=123)

# Web: Unique session per user
chat_service = ChatService()  # Auto-generates UUID
```

### Memory Features
- **Conversation History**: Automatic storage of agent interactions
- **Context Awareness**: Agents reference previous questions and results
- **Follow-up Support**: "What about by department?" after asking about regions
- **Session Isolation**: Multiple users don't interfere with each other

## 🌐 Interface Architecture

### ✅ Terminal Interface (`main.py`) - **CURRENTLY WORKING**
- **Pattern**: Follows `agentic_app_quickstart/examples/` patterns exactly
- **Features**: 
  - Direct CLI interaction with full agent system
  - Simple session management (`session_id=123`)
  - All 6 agents with complete handoff relationships
  - Automatic data loading from `data/` folder
  - Memory-enabled follow-up questions
- **Usage**: `uv run python main.py`
- **Status**: ✅ **Ready for use and demonstration**

### 🚧 Web Interface (`gradio_app.py`) - **FUTURE IMPLEMENTATION**
- **Status**: **Not yet implemented** - placeholder for future development
- **Planned Features**: 
  - Modern UI with professional design
  - Multi-user support with isolated sessions
  - Chart generation and export functionality
  - Side-by-side chat and visualization panels
- **Timeline**: Will be implemented in later project phases
- **Note**: Currently non-functional - use terminal interface instead

### ✅ Chat Service Layer (`chat_service.py`) - **DESIGN CHOICE**

#### Why a Shared Service Layer?
The `ChatService` class was designed as an abstraction layer for several strategic reasons:

1. **Interface Agnostic**: Same business logic works for both terminal and future web interfaces
2. **Consistent Behavior**: Users get identical responses regardless of interface choice
3. **Clean Separation**: UI concerns separated from agent logic and data processing
4. **Future-Proof**: Easy to add new interfaces (API, mobile app) without duplicating logic
5. **Testable**: Business logic can be tested independently of UI frameworks

#### Current Implementation:
```python
# Terminal uses ChatService directly
chat_service = ChatService()  # Auto-generates UUID
await chat_service.initialize_data()  # Loads sample data
result = await chat_service.send_message(user_input)  # Processes through agents
```

#### Key Features:
- **Session Management**: UUID-based sessions for multi-user support
- **Error Handling**: Comprehensive exception management with user-friendly messages
- **Guardrail Integration**: Input/output filtering built into the service layer
- **Memory Management**: Automatic conversation history storage
- **Data Initialization**: Automatic CSV loading with progress feedback

## 📊 Visualization & Charts System

### Comprehensive Chart Generation
The system now includes a complete visualization pipeline with 7 chart types and intelligent chart selection.

#### 🎨 **Available Chart Types**
| Chart Type | Best For | Example Request |
|---|---|---|
| **Bar Charts** | Categorical comparisons | "Create a bar chart of sales by product" |
| **Line Plots** | Trends over time | "Show temperature trends over time" |
| **Histograms** | Data distributions | "Generate a histogram of employee salaries" |
| **Pie Charts** | Proportions & percentages | "Make a pie chart of sales by region" |
| **Scatter Plots** | Variable relationships | "Create a scatter plot of price vs quantity" |
| **Box Plots** | Distribution analysis | "Show salary distribution by department" |
| **Heatmaps** | Correlation matrices | "Generate a correlation heatmap of numeric data" |

#### 🧠 **Intelligent Chart Selection**
- **Automatic Analysis**: System analyzes your data structure to suggest optimal chart types
- **Multiple Suggestions**: Get several chart options for your data
- **Smart Recommendations**: Analytics Agent decides when visualization would be helpful
- **Clear Reasoning**: Each suggestion comes with explanation of why it's appropriate


#### 📁 **File Management**
- **Auto-generated filenames**: `chart_type_title_timestamp_id.png`
- **Storage location**: `/charts/` directory
- **Full file paths**: Complete paths provided for easy access
- **Session cleanup**: Chart files automatically cleaned up after session ends

#### ❌ **Unsupported Chart Types**
If you request unsupported charts (area charts, bubble charts, treemaps, etc.), the system will:
- Clearly explain available chart types
- Suggest the best supported alternative
- Provide reasoning for the recommendation

#### 💡 **Example Visualization Requests**
```bash
# Categorical Analysis
"Create a bar chart of total sales by product"
"Show me a pie chart of employee distribution by department"

# Relationship Analysis  
"Generate a scatter plot of salary vs performance score"
"Create a correlation heatmap of all numeric columns in weather data"

# Distribution Analysis
"Make a histogram of all product prices"
"Show box plots of temperature by city"

# Trend Analysis
"Create a line plot of sales over time"
"Plot temperature trends by date"
```

### 🛠️ **Implementation Details**

#### **Architecture Components**
1. **Analytics Agent** (`csv_agents.py`):
   - Acts as visualization gatekeeper
   - Decides when data should be visualized
   - Retrieves raw data using `execute_sql_query()`
   - Hands off to Visualization Agent with JSON data

2. **Visualization Agent** (`csv_agents.py`):
   - Receives JSON data from Analytics Agent
   - Analyzes data structure for optimal chart type
   - Creates actual PNG chart files using matplotlib
   - Returns full file paths for user access

3. **Visualization Core** (`visualization_core.py`):
   - 7 chart creation functions (bar, line, histogram, pie, scatter, box, heatmap)
   - Data analysis and chart type suggestion logic
   - File management and unique naming system
   - Error handling for invalid data structures

#### **Actual Data Flow**
```python
# 1. User requests visualization
"Create a bar chart of sales by product"

# 2. Communication Agent routes to Analytics Agent
# Analytics Agent recognizes visualization request

# 3. Analytics Agent gets data using SQL tools
execute_sql_query("SELECT product, SUM(price*quantity) as total_sales FROM sample_sales GROUP BY product")

# 4. Analytics Agent decides to create visualization
# Framework automatically hands off to Visualization Agent (based on agent.handoffs configuration)

# 5. Visualization Agent receives context and creates chart
# Uses create_bar_chart() tool with the data from previous context

# 6. Chart file created with unique name
/charts/bar_chart_Sales_by_Product_20250818_205441_932eba16.png

# 7. Visualization Agent returns to Communication Agent
# Communication Agent presents final result to user
```

#### **Session Management**
- **Chart Storage**: Files saved to `/charts/` directory with unique timestamps
- **Automatic Cleanup**: All chart files removed when session ends (`chat_service.close_session()`)
- **Memory Management**: No persistent storage, prevents disk space accumulation
- **Error Handling**: Graceful cleanup even if individual file removal fails

#### **Implementation Notes**
- **Agent Handoffs**: The agentic framework handles handoffs automatically based on `agent.handoffs` configuration
- **Context Passing**: Data flows through conversation context rather than explicit message formatting
- **Visualization Trigger**: Analytics Agent's instructions determine when to involve Visualization Agent
- **Chart Creation**: Visualization Agent uses conversation context to access data from previous SQL queries

## ❓ Supported Question Types

### Basic Statistics
- "What's the average salary in the employee data?"
- "How many employees work in the Engineering department?"
- "What's the total sales for the month of January?"

### Data Exploration  
- "What datasets are available?"
- "What columns are in the sales data?"
- "Show me the structure of the weather data"

### Complex Analysis
- "What's the average sales by product category?"
- "Show me employee count by department and salary range"
- "Which month had the highest total sales?"

### Comparative Queries
- "Compare average salaries between departments"
- "What's the sales trend by month?"
- "How do temperatures vary by city?"

### Follow-up Questions (Memory-Enabled)
- User: "What's the average price?"
- System: "$287.45"  
- User: "What about by category?" ← References previous context
- System: Provides breakdown by category

### Visualization Requests
- "Show me a chart of sales by month"
- "Create a histogram of employee salaries"  
- "Plot temperature vs humidity"
- "Visualize department sizes"

## 🚀 Quick Start

### Prerequisites
```bash
# Install dependencies
uv sync

# Set up environment
echo "OPENAI_API_KEY=your_key" > .env
echo "PHEONIX_API_KEY=your_phoenix_key" >> .env  # Optional for tracing
```

### ✅ Terminal Interface (Ready to Use)
```bash
cd week_1/solution  
uv run python main.py
# Fully functional with all agents, memory, and sample data
```

### 🚧 Web Interface (Future Implementation)
```bash
# NOTE: Web interface not yet implemented
# cd week_1/solution
# uv run python gradio_app.py  # ← This will be available in future phases
# Currently use terminal interface instead
```

## 🧪 Testing

### Unit Tests
```bash
uv run pytest tests/unit/ -v
# Tests individual function tools, data loading, SQL execution
```

### Integration Tests
```bash
uv run pytest tests/integration/ -v
# Tests agent interactions, handoff relationships, service layer integration
```

### End-to-End Tests
```bash  
uv run pytest tests/e2e/ -v
# Tests complete user workflows, memory persistence, error scenarios
```

### Run All Tests
```bash
uv run pytest tests/ -v
# Runs unit, integration, and e2e tests with coverage reporting
```

## ✨ Key Features Summary

### 🎯 **Deterministic Processing**
- Predictable query flow through specialized agents
- Systematic validation and error recovery
- Consistent, reliable results for users

### 🛡️ **Intelligent Guardrails**
- Input filtering for analytics-only questions
- Output validation to prevent topic drift
- Graceful error handling with helpful messages

### 🧠 **Advanced Memory**
- Multi-user session management
- Context-aware follow-up questions
- Conversation history across agent handoffs

### 🌐 **Multi-Interface Design**
- Shared business logic between terminal and web
- Modern, responsive web UI with visualizations
- Professional appearance suitable for business use

### 📊 **Comprehensive Analytics**
- Automatic data loading and type detection
- Statistical analysis and SQL query capabilities
- Chart generation and export functionality
- Schema discovery and data exploration tools

## 🎯 **Getting Started - What Works Now**

### ✅ **Ready to Use Today:**
1. **Run the terminal interface**: `uv run python main.py` 
2. **Try sample questions**: "What datasets are available?", "What's the average salary?"
3. **Test memory**: Ask follow-up questions like "What about by department?"
4. **Explore all agents**: Complex queries will use the full SQL pipeline
5. **Run tests**: `uv run pytest tests/ -v` to see comprehensive test coverage

### 🚧 **Coming in Future Phases:**
- Web interface with modern UI and visualizations
- Chart generation and export features  
- Multi-user web sessions

---

This implementation demonstrates a production-ready multi-agent system with enterprise-level features including deterministic workflows, intelligent guardrails, comprehensive memory management, and extensive testing. The terminal interface is fully functional and ready for demonstration and use.
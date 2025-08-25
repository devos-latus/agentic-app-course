"""
Comprehensive Week 2 Test Suite

Runs all major test scenarios using Week 2 EnhancedChatService to generate
extensive Phoenix tracing logs. This combines all test patterns from the
existing test suite but uses the enhanced implementation.
"""

import pytest
import os
import tempfile
import sys
import warnings
from pathlib import Path

# Add Week 2 solution directory first, then Week 1 as fallback
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "week_2" / "solution"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "week_1" / "solution"))
sys.path.insert(0, str(Path(__file__).parent.parent))

# Suppress warnings
warnings.filterwarnings("ignore", category=DeprecationWarning, module="pydantic")

# Import Week 2 enhanced components
from enhanced_chat_service import EnhancedChatService, initialize_enhanced_chat_service
import tools
# from helpers.llm_judge import evaluate_response_quality, ResponseQuality


class TestWeek2ComprehensiveFunctionality:
    """Comprehensive test suite using Week 2 EnhancedChatService."""

    def setup_method(self):
        """Set up comprehensive test environment."""
        self.temp_dir = tempfile.mkdtemp()

        # Create multiple realistic CSV files for comprehensive testing
        self.create_sales_data()
        self.create_employee_data()
        self.create_inventory_data()
        self.create_customer_data()

        # Initialize enhanced service
        self.service = None

    def create_sales_data(self):
        """Create comprehensive sales data."""
        self.sales_csv = os.path.join(self.temp_dir, "sales_transactions.csv")
        with open(self.sales_csv, "w") as f:
            f.write("""transaction_id,date,product,category,price,quantity,customer_id,sales_rep,region
TXN001,2024-01-15,Laptop Pro,Electronics,1299.99,1,CUST001,Alice Johnson,West
TXN002,2024-01-16,Wireless Mouse,Electronics,49.99,3,CUST002,Bob Smith,East
TXN003,2024-01-17,Mechanical Keyboard,Electronics,129.99,2,CUST003,Carol Davis,North
TXN004,2024-01-18,4K Monitor,Electronics,399.99,1,CUST004,David Wilson,South
TXN005,2024-01-19,Tablet,Electronics,599.99,1,CUST005,Alice Johnson,West
TXN006,2024-01-20,Bluetooth Headphones,Electronics,199.99,2,CUST006,Bob Smith,East
TXN007,2024-01-21,Gaming Chair,Furniture,299.99,1,CUST007,Carol Davis,North
TXN008,2024-01-22,Standing Desk,Furniture,449.99,1,CUST008,David Wilson,South
TXN009,2024-01-23,Webcam HD,Electronics,89.99,4,CUST009,Alice Johnson,West
TXN010,2024-01-24,USB-C Hub,Electronics,79.99,2,CUST010,Bob Smith,East""")

    def create_employee_data(self):
        """Create comprehensive employee data."""
        self.employees_csv = os.path.join(self.temp_dir, "employee_records.csv")
        with open(self.employees_csv, "w") as f:
            f.write("""employee_id,name,department,position,salary,hire_date,performance_rating,manager_id,location
EMP001,Alice Johnson,Sales,Senior Sales Rep,85000,2022-03-15,4.5,MGR001,San Francisco
EMP002,Bob Smith,Sales,Sales Rep,65000,2021-07-20,4.2,MGR001,New York
EMP003,Carol Davis,Engineering,Senior Engineer,120000,2020-01-10,4.8,MGR002,Seattle
EMP004,David Wilson,Marketing,Marketing Manager,95000,2023-01-05,4.1,MGR003,Chicago
EMP005,Eva Brown,Engineering,Lead Engineer,135000,2019-05-12,4.9,MGR002,Seattle
EMP006,Frank Miller,Sales,Sales Manager,110000,2021-11-08,4.6,MGR001,Boston
EMP007,Grace Lee,HR,HR Specialist,70000,2022-09-14,4.3,MGR004,Austin
EMP008,Henry Clark,Finance,Financial Analyst,75000,2023-02-20,4.0,MGR005,Denver""")

    def create_inventory_data(self):
        """Create comprehensive inventory data."""
        self.inventory_csv = os.path.join(self.temp_dir, "inventory_status.csv")
        with open(self.inventory_csv, "w") as f:
            f.write("""product_id,product_name,category,current_stock,reorder_level,max_capacity,supplier,unit_cost,last_restocked
PROD001,Laptop Pro,Electronics,15,10,50,TechSupplier Inc,800.00,2024-01-20
PROD002,Wireless Mouse,Electronics,85,25,200,TechSupplier Inc,25.00,2024-01-18
PROD003,Mechanical Keyboard,Electronics,42,15,100,KeyboardCorp,75.00,2024-01-19
PROD004,4K Monitor,Electronics,28,12,60,DisplayTech Ltd,250.00,2024-01-17
PROD005,Tablet,Electronics,22,8,40,TabletMakers Co,400.00,2024-01-21
PROD006,Bluetooth Headphones,Electronics,67,20,150,AudioGear Inc,120.00,2024-01-16
PROD007,Gaming Chair,Furniture,8,5,30,ComfortSeating,180.00,2024-01-15
PROD008,Standing Desk,Furniture,12,6,25,OfficeFurniture Co,280.00,2024-01-22""")

    def create_customer_data(self):
        """Create comprehensive customer data."""
        self.customers_csv = os.path.join(self.temp_dir, "customer_profiles.csv")
        with open(self.customers_csv, "w") as f:
            f.write("""customer_id,name,email,phone,address,city,state,zip_code,registration_date,customer_type,total_purchases
CUST001,John Doe,john.doe@email.com,555-0101,123 Main St,San Francisco,CA,94102,2023-06-15,Premium,2599.98
CUST002,Jane Smith,jane.smith@email.com,555-0102,456 Oak Ave,New York,NY,10001,2023-07-20,Standard,149.97
CUST003,Mike Johnson,mike.j@email.com,555-0103,789 Pine Rd,Seattle,WA,98101,2023-08-10,Premium,259.98
CUST004,Sarah Wilson,sarah.w@email.com,555-0104,321 Elm St,Chicago,IL,60601,2023-09-05,Standard,399.99
CUST005,Tom Brown,tom.brown@email.com,555-0105,654 Maple Dr,Austin,TX,73301,2023-10-12,Premium,599.99
CUST006,Lisa Davis,lisa.d@email.com,555-0106,987 Cedar Ln,Boston,MA,02101,2023-11-18,Standard,399.98
CUST007,Chris Miller,chris.m@email.com,555-0107,147 Birch Way,Denver,CO,80201,2023-12-03,Premium,299.99
CUST008,Amy Taylor,amy.t@email.com,555-0108,258 Spruce St,Miami,FL,33101,2024-01-08,Standard,449.99""")

    @pytest.mark.asyncio
    async def test_01_enhanced_service_initialization(self):
        """Test enhanced service initialization with tracing."""
        print("\n🔍 Test 1: Enhanced Service Initialization")

        self.service = await initialize_enhanced_chat_service()

        assert self.service is not None
        assert isinstance(self.service, EnhancedChatService)

        analytics = self.service.get_session_analytics()
        assert analytics["enhanced_tracing_enabled"] is True
        assert analytics["phoenix_project"] == "analytics_system"

        print(f"✅ Session ID: {analytics['session_id']}")
        print(f"✅ Enhanced tracing: {analytics['enhanced_tracing_enabled']}")

    @pytest.mark.asyncio
    async def test_02_comprehensive_data_loading(self):
        """Test loading all CSV files with enhanced tracing."""
        print("\n📁 Test 2: Comprehensive Data Loading")

        if not self.service:
            self.service = await initialize_enhanced_chat_service()

        # Load all test data
        result = tools._discover_and_load_csv_files(self.temp_dir)

        assert result["success"] is True
        assert result["successfully_loaded"] == 4  # All 4 CSV files

        print(f"✅ Loaded {result['successfully_loaded']} datasets")
        for file_info in result["loaded_files"]:
            print(f"  - {file_info['table_name']}: {file_info['row_count']} rows")

    @pytest.mark.asyncio
    async def test_03_data_discovery_conversations(self):
        """Test data discovery with multiple conversation turns."""
        print("\n🤖 Test 3: Data Discovery Conversations")

        if not self.service:
            self.service = await initialize_enhanced_chat_service()

        tools._discover_and_load_csv_files(self.temp_dir)

        discovery_questions = [
            "What datasets are available for analysis?",
            "Tell me about the structure of each table",
            "What are the key columns in the sales data?",
            "How many records are in each dataset?",
            "What types of analysis can I perform with this data?",
        ]

        for i, question in enumerate(discovery_questions):
            print(f"  Question {i+1}: {question}")
            result = await self.service.send_message(question)

            assert result is not None
            assert result.get("success", False) or "response" in result

        analytics = self.service.get_session_analytics()
        assert analytics["conversation_count"] == len(discovery_questions)
        print(f"✅ Completed {analytics['conversation_count']} discovery conversations")

    @pytest.mark.asyncio
    async def test_04_sales_analysis_workflow(self):
        """Test comprehensive sales analysis workflow."""
        print("\n📊 Test 4: Sales Analysis Workflow")

        if not self.service:
            self.service = await initialize_enhanced_chat_service()

        tools._discover_and_load_csv_files(self.temp_dir)

        sales_questions = [
            "What are the total sales by region?",
            "Who are the top performing sales representatives?",
            "What products generate the most revenue?",
            "Show me sales trends by category",
            "What's the average transaction value?",
            "Which customers have made the largest purchases?",
            "Calculate the sales performance by month",
        ]

        for i, question in enumerate(sales_questions):
            print(f"  Analysis {i+1}: {question}")
            result = await self.service.send_message(question)
            assert result is not None

        print(f"✅ Completed {len(sales_questions)} sales analysis queries")

    @pytest.mark.asyncio
    async def test_05_employee_analysis_workflow(self):
        """Test employee data analysis workflow."""
        print("\n👥 Test 5: Employee Analysis Workflow")

        if not self.service:
            self.service = await initialize_enhanced_chat_service()

        tools._discover_and_load_csv_files(self.temp_dir)

        hr_questions = [
            "What's the average salary by department?",
            "Show me performance ratings distribution",
            "Which employees have the highest performance ratings?",
            "What's the relationship between salary and performance?",
            "How many employees are in each location?",
            "Who are the newest hires?",
            "Calculate average tenure by department",
        ]

        for question in hr_questions:
            result = await self.service.send_message(question)
            assert result is not None

        print(f"✅ Completed {len(hr_questions)} HR analysis queries")

    @pytest.mark.asyncio
    async def test_06_inventory_management_workflow(self):
        """Test inventory management analysis."""
        print("\n📦 Test 6: Inventory Management Workflow")

        if not self.service:
            self.service = await initialize_enhanced_chat_service()

        tools._discover_and_load_csv_files(self.temp_dir)

        inventory_questions = [
            "Which products are below reorder level?",
            "What's the total inventory value?",
            "Show me stock levels by category",
            "Which suppliers provide the most products?",
            "What's the average unit cost by category?",
            "Identify products that need immediate restocking",
        ]

        for question in inventory_questions:
            result = await self.service.send_message(question)
            assert result is not None

        print(f"✅ Completed {len(inventory_questions)} inventory queries")

    @pytest.mark.asyncio
    async def test_07_visualization_requests(self):
        """Test various visualization requests."""
        print("\n📈 Test 7: Visualization Requests")

        if not self.service:
            self.service = await initialize_enhanced_chat_service()

        tools._discover_and_load_csv_files(self.temp_dir)

        viz_requests = [
            "Create a bar chart of sales by region",
            "Generate a pie chart of employees by department",
            "Show a scatter plot of salary vs performance rating",
            "Create a line chart of sales over time",
            "Make a histogram of product prices",
            "Generate a bar chart of inventory levels by category",
        ]

        for request in viz_requests:
            result = await self.service.send_message(request)
            assert result is not None

        print(f"✅ Completed {len(viz_requests)} visualization requests")

    @pytest.mark.asyncio
    async def test_08_error_handling_scenarios(self):
        """Test various error scenarios with enhanced tracing."""
        print("\n⚠️  Test 8: Error Handling Scenarios")

        if not self.service:
            self.service = await initialize_enhanced_chat_service()

        tools._discover_and_load_csv_files(self.temp_dir)

        error_scenarios = [
            "Show me data from nonexistent_table",
            "Calculate the square root of the product name",
            "Create a chart with invalid column names",
            "What's the correlation between colors and numbers?",
            "Show me sales data for the year 3000",
            "Calculate the average of text fields",
        ]

        for scenario in error_scenarios:
            result = await self.service.send_message(scenario)
            # Should handle errors gracefully
            assert result is not None

        print(f"✅ Tested {len(error_scenarios)} error scenarios")

    @pytest.mark.asyncio
    async def test_09_memory_and_context_workflow(self):
        """Test conversation memory and context handling."""
        print("\n🧠 Test 9: Memory and Context Workflow")

        if not self.service:
            self.service = await initialize_enhanced_chat_service()

        tools._discover_and_load_csv_files(self.temp_dir)

        # Test contextual conversation
        context_flow = [
            "What datasets do we have?",
            "Tell me more about the first one you mentioned",
            "Show me some statistics from that table",
            "Can you create a visualization of the data we just discussed?",
            "What insights can you draw from this analysis?",
            "How does this compare to the other datasets?",
        ]

        for question in context_flow:
            result = await self.service.send_message(question)
            assert result is not None

        print(f"✅ Completed {len(context_flow)} contextual conversations")

    @pytest.mark.asyncio
    async def test_10_comprehensive_session_analytics(self):
        """Test comprehensive session analytics."""
        print("\n📊 Test 10: Session Analytics")

        if not self.service:
            self.service = await initialize_enhanced_chat_service()

        # Send a few more messages to build up analytics
        for i in range(3):
            await self.service.send_message(f"Test analytics message {i+1}")

        analytics = self.service.get_session_analytics()

        print("📊 Final Session Analytics:")
        print(f"  Session ID: {analytics['session_id']}")
        print(f"  Total conversations: {analytics['conversation_count']}")
        print(f"  Data loaded: {analytics['data_loaded']}")
        print(f"  Enhanced tracing: {analytics['enhanced_tracing_enabled']}")
        print(f"  Phoenix project: {analytics['phoenix_project']}")

        assert analytics["conversation_count"] > 0
        assert analytics["enhanced_tracing_enabled"] is True
        assert analytics["phoenix_project"] == "analytics_system"

        print("✅ Session analytics validated")

    def teardown_method(self):
        """Clean up after each test."""
        if self.service:
            try:
                self.service.close_session()
            except:
                pass


if __name__ == "__main__":
    print("🔍 Week 2 Comprehensive Test Suite")
    print("This will generate extensive Phoenix tracing logs!")
    print("Check your Phoenix dashboard during execution.")
    print("=" * 60)

    # Run the tests
    pytest.main([__file__, "-v", "-s"])

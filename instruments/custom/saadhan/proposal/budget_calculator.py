"""
Budget Calculator for Proposal Development Instrument
Handles budget calculations and financial planning
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict

@dataclass
class BudgetItem:
    """Budget item data structure"""
    id: str
    category: str
    description: str
    unit: str
    quantity: float
    unit_cost: float
    total_cost: float
    frequency: str
    duration: int
    notes: str

@dataclass
class Budget:
    """Budget data structure"""
    id: str
    proposal_id: str
    total_amount: float
    currency: str
    categories: Dict[str, float]
    items: List[BudgetItem]
    overhead_rate: float
    contingency_rate: float
    notes: str
    created_at: str
    updated_at: str
    status: str

class BudgetCalculator:
    def __init__(self, workspace_root: str):
        """
        Initialize budget calculator
        Args:
            workspace_root: Path to workspace root directory
        """
        self.workspace_root = workspace_root
        self.budgets_dir = os.path.join(workspace_root, 'budgets')
        self._ensure_directories()

        # Standard budget categories
        self.categories = {
            'personnel': 'Staff and human resources costs',
            'equipment': 'Equipment and machinery',
            'materials': 'Materials and supplies',
            'travel': 'Travel and transportation',
            'training': 'Training and capacity building',
            'services': 'Professional services',
            'infrastructure': 'Infrastructure development',
            'monitoring': 'Monitoring and evaluation',
            'admin': 'Administrative costs'
        }

    def _ensure_directories(self):
        """Ensure required directories exist"""
        os.makedirs(self.budgets_dir, exist_ok=True)

    def create_budget(self, proposal_id: str, budget_data: Dict) -> Budget:
        """
        Create a new budget
        Args:
            proposal_id: Associated proposal ID
            budget_data: Dictionary containing budget information
        Returns:
            Budget object
        """
        try:
            budget_id = f"BUD_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Create budget items
            items = [
                BudgetItem(
                    id=f"ITEM_{i}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    category=item['category'],
                    description=item['description'],
                    unit=item['unit'],
                    quantity=item['quantity'],
                    unit_cost=item['unit_cost'],
                    total_cost=item['quantity'] * item['unit_cost'] * item.get('duration', 1),
                    frequency=item.get('frequency', 'one-time'),
                    duration=item.get('duration', 1),
                    notes=item.get('notes', '')
                )
                for i, item in enumerate(budget_data['items'])
            ]

            # Calculate category totals
            categories = self._calculate_category_totals(items)
            
            # Calculate total amount
            subtotal = sum(item.total_cost for item in items)
            overhead = subtotal * budget_data.get('overhead_rate', 0.0)
            contingency = subtotal * budget_data.get('contingency_rate', 0.0)
            total = subtotal + overhead + contingency

            budget = Budget(
                id=budget_id,
                proposal_id=proposal_id,
                total_amount=total,
                currency=budget_data['currency'],
                categories=categories,
                items=items,
                overhead_rate=budget_data.get('overhead_rate', 0.0),
                contingency_rate=budget_data.get('contingency_rate', 0.0),
                notes=budget_data.get('notes', ''),
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat(),
                status='draft'
            )

            self._save_budget(budget)
            return budget

        except Exception as e:
            raise Exception(f"Failed to create budget: {str(e)}")

    def update_budget(self, budget_id: str, updates: Dict) -> Budget:
        """
        Update budget information
        Args:
            budget_id: Budget identifier
            updates: Dictionary containing updates
        Returns:
            Updated Budget object
        """
        budget = self.get_budget(budget_id)
        if budget is None:
            raise Exception("Budget not found")

        try:
            if 'items' in updates:
                # Update items
                items = [
                    BudgetItem(
                        id=f"ITEM_{i}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                        category=item['category'],
                        description=item['description'],
                        unit=item['unit'],
                        quantity=item['quantity'],
                        unit_cost=item['unit_cost'],
                        total_cost=item['quantity'] * item['unit_cost'] * item.get('duration', 1),
                        frequency=item.get('frequency', 'one-time'),
                        duration=item.get('duration', 1),
                        notes=item.get('notes', '')
                    )
                    for i, item in enumerate(updates['items'])
                ]
                budget.items = items
                
                # Recalculate category totals
                budget.categories = self._calculate_category_totals(items)
                
                # Recalculate total amount
                subtotal = sum(item.total_cost for item in items)
                overhead = subtotal * budget.overhead_rate
                contingency = subtotal * budget.contingency_rate
                budget.total_amount = subtotal + overhead + contingency

            # Update other attributes
            for key, value in updates.items():
                if key != 'items' and hasattr(budget, key):
                    setattr(budget, key, value)

            budget.updated_at = datetime.now().isoformat()
            self._save_budget(budget)
            return budget

        except Exception as e:
            raise Exception(f"Failed to update budget: {str(e)}")

    def get_budget(self, budget_id: str) -> Optional[Budget]:
        """
        Retrieve budget by ID
        Args:
            budget_id: Budget identifier
        Returns:
            Budget object if found, None otherwise
        """
        budget_file = os.path.join(self.budgets_dir, f"{budget_id}.json")
        if not os.path.exists(budget_file):
            return None

        try:
            with open(budget_file, 'r') as f:
                data = json.load(f)
                # Convert items data to BudgetItem objects
                data['items'] = [BudgetItem(**item) for item in data['items']]
                return Budget(**data)
        except Exception as e:
            raise Exception(f"Failed to load budget: {str(e)}")

    def _calculate_category_totals(self, items: List[BudgetItem]) -> Dict[str, float]:
        """Calculate total amount for each budget category"""
        totals = {}
        for item in items:
            if item.category not in totals:
                totals[item.category] = 0
            totals[item.category] += item.total_cost
        return totals

    def _save_budget(self, budget: Budget):
        """Save budget data to file"""
        budget_file = os.path.join(self.budgets_dir, f"{budget.id}.json")
        with open(budget_file, 'w') as f:
            # Convert to dictionary and handle BudgetItem objects
            budget_dict = asdict(budget)
            budget_dict['items'] = [asdict(item) for item in budget.items]
            json.dump(budget_dict, f, indent=2)

    def generate_summary(self, budget_id: str) -> Dict:
        """
        Generate budget summary
        Args:
            budget_id: Budget identifier
        Returns:
            Dictionary containing summary information
        """
        budget = self.get_budget(budget_id)
        if budget is None:
            raise Exception("Budget not found")

        # Calculate percentages
        total = budget.total_amount
        category_percentages = {
            category: (amount / total) * 100
            for category, amount in budget.categories.items()
        }

        return {
            'id': budget.id,
            'proposal_id': budget.proposal_id,
            'total_amount': budget.total_amount,
            'currency': budget.currency,
            'category_breakdown': {
                category: {
                    'amount': amount,
                    'percentage': category_percentages[category]
                }
                for category, amount in budget.categories.items()
            },
            'overhead_amount': budget.total_amount * budget.overhead_rate,
            'contingency_amount': budget.total_amount * budget.contingency_rate,
            'item_count': len(budget.items),
            'status': budget.status,
            'last_updated': budget.updated_at
        }

    def validate_budget(self, budget: Budget) -> List[str]:
        """
        Validate budget data
        Args:
            budget: Budget object to validate
        Returns:
            List of validation errors
        """
        if not budget:
            return ["Budget object cannot be None"]

        errors = []

        try:
            # Check for negative values
            if not isinstance(budget.total_amount, (int, float)):
                errors.append("Total amount must be a number")
            elif budget.total_amount < 0:
                errors.append("Total amount cannot be negative")

            if not isinstance(budget.overhead_rate, (int, float)):
                errors.append("Overhead rate must be a number")
            elif budget.overhead_rate < 0 or budget.overhead_rate > 1:
                errors.append("Overhead rate must be between 0 and 1")

            if not isinstance(budget.contingency_rate, (int, float)):
                errors.append("Contingency rate must be a number")
            elif budget.contingency_rate < 0 or budget.contingency_rate > 1:
                errors.append("Contingency rate must be between 0 and 1")

            # Validate items
            if not budget.items:
                errors.append("Budget must contain at least one item")
            else:
                for i, item in enumerate(budget.items, 1):
                    if not item.description:
                        errors.append(f"Item {i} is missing a description")
                    
                    if not isinstance(item.quantity, (int, float)):
                        errors.append(f"Item {i} ({item.description}): quantity must be a number")
                    elif item.quantity <= 0:
                        errors.append(f"Item {i} ({item.description}): quantity must be greater than 0")
                    
                    if not isinstance(item.unit_cost, (int, float)):
                        errors.append(f"Item {i} ({item.description}): unit cost must be a number")
                    elif item.unit_cost < 0:
                        errors.append(f"Item {i} ({item.description}): unit cost cannot be negative")
                    
                    if not isinstance(item.duration, (int, float)):
                        errors.append(f"Item {i} ({item.description}): duration must be a number")
                    elif item.duration < 1:
                        errors.append(f"Item {i} ({item.description}): duration must be at least 1")
                    
                    if not item.category:
                        errors.append(f"Item {i} ({item.description}): category is required")
                    elif item.category not in self.categories:
                        errors.append(f"Item {i} ({item.description}): invalid category '{item.category}'")

            # Validate category totals
            if hasattr(budget, 'categories'):
                calculated_totals = self._calculate_category_totals(budget.items)
                if calculated_totals != budget.categories:
                    errors.append("Category totals do not match item calculations")

            # Validate total amount with more detailed error messages
            subtotal = sum(item.total_cost for item in budget.items)
            overhead = subtotal * budget.overhead_rate
            contingency = subtotal * budget.contingency_rate
            expected_total = subtotal + overhead + contingency

            if abs(expected_total - budget.total_amount) > 0.01:  # Allow small floating-point differences
                errors.append(
                    f"Total amount mismatch: expected {expected_total:.2f} "
                    f"(subtotal: {subtotal:.2f} + overhead: {overhead:.2f} + "
                    f"contingency: {contingency:.2f}), but got {budget.total_amount:.2f}"
                )

        except Exception as e:
            errors.append(f"Unexpected error during budget validation: {str(e)}")

        return errors 
"""Create an agent, a tool for it, and answer a phone number with it.

    DIALGEM_API_KEY=zk_... python examples/provision_agent.py +14155550100
"""

import sys

from dialgem import Dialgem

dialgem = Dialgem()

agent = dialgem.agents.create(
    name="Front desk",
    system_prompt="You are the front desk for {{business_name}}. Be brief.",
    first_message="Thanks for calling, how can I help?",
    default_dynamic_variables={"business_name": "Acme Dental"},
)

dialgem.agents.functions.create(
    agent.id,
    name="lookup_order",
    url="https://example.com/api/orders/lookup",
    parameters={"type": "object", "properties": {"order_id": {"type": "string"}}},
)

number = dialgem.phone_numbers.create(phone_number=sys.argv[1])
dialgem.phone_numbers.update(number.id, inbound_agent_id=agent.id, set_inbound_agent=True)
print(f"{number.phone_number} now answers with agent {agent.id}")

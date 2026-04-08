import time

def deploy(context, payload):
    """
    Huntsman sub-routine for Gumroad product creation.
    """
    page = context.new_page()
    
    # 1. INFILTRATION (Login)
    print("   > Navigating to Gumroad Login...")
    page.goto("https://gumroad.com/login")
    
    # Check for login requirement
    if page.is_visible('input[name="email"]'):
        print("   ⚠️  LOGIN REQUIRED! Please log in to Gumroad manually within 30 seconds...")
        try:
            page.wait_for_url("**/dashboard", timeout=45000)
            print("   > Login confirmed.")
        except:
            print("   > Login timeout. Proceeding (session might be saved).")

    # 2. EXECUTION (Create Product)
    print("   > Initializing New Product...")
    page.goto("https://gumroad.com/products/new")
    
    # Product Name
    page.fill('input[name="name"]', payload['product_name'])
    
    # Product Type -> "Digital Product"
    try:
        page.click('div:has-text("Digital product")', timeout=2000)
    except:
        page.click('text="Digital product"')

    # Price
    price_val = str(payload['price_usd']).replace('$','')
    page.fill('input[name="price"]', price_val)
    
    print("   > Draft initialized. Moving to customization...")
    page.click('text="Next: Customize"')
    
    # 3. CUSTOMIZATION
    # Wait for editor
    page.wait_for_selector('textarea[name="description"]', state="attached", timeout=10000)
    
    # Description
    page.fill('textarea[name="description"]', payload['description_markdown'])
    
    # Capture Draft URL
    product_url = page.url
    print(f"   > Product Draft created at: {product_url}")
    
    # 4. SAVE (Do not publish yet, wait for Human Attestation)
    page.click('text="Save changes"')
    time.sleep(2)
    
    return {"status": "success", "url": product_url}

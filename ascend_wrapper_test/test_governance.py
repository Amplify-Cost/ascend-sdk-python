import boto3
import logging
from botocore.exceptions import ClientError
from ascend_boto3 import enable_governance, disable_governance
import os

# --- Configuration ---
# SEC-113: Read API key from environment variable for security
# Set your API key: export ASCEND_API_KEY=owkai_xxx_your_key_here
ASCEND_API_KEY = os.environ.get("ASCEND_API_KEY")
if not ASCEND_API_KEY:
    raise ValueError("ASCEND_API_KEY environment variable is required. Set it with: export ASCEND_API_KEY=your_key")

# SEC-113: Governance endpoint is POST /api/v1/actions/submit (handled by wrapper.py)
TEST_BUCKET_NAME = "my-temp-ascend-governance-test-12345"
TEST_REGION = 'us-west-2'  # Using a specific region to prevent IllegalLocationConstraintException
# ---------------------

# Configure logging to see the wrapper's output
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - [Ascend Governance] - %(message)s',
                    datefmt='%H:%M:%S')

def run_test():
    """Runs the end-to-end functional test of the Boto3 wrapper."""
    
    print("\n" + "="*55)
    print("🚀 Starting Ascend Boto3 Wrapper Functional Test (v1.0.0)")
    print("="*55)
    
    s3_client = None
    
    try:
        # --- 1. Enable Governance ---
        print("\n--- 1. Enabling Ascend Governance Hook ---")
        enable_governance(
            api_key=ASCEND_API_KEY,
            base_url="https://pilot.owkai.app", 
            agent_name="Boto3-Wrapper-Validation-Agent"
        )
        
        # Initialize Boto3 client with the wrapper hook active
        s3_client = boto3.client('s3', region_name=TEST_REGION)

        # --- 2. Test LOW Risk Action (Should Auto-Approve Locally) ---
        print("\n--- 2. Testing LOW Risk Action (s3:list_buckets) ---")
        logging.info("Attempting s3.list_buckets(). Expecting local Auto-Approval...")
        
        # Low-risk actions are classified locally by the wrapper and should pass instantly.
        response = s3_client.list_buckets()
        logging.info(f"SUCCESS: s3.list_buckets passed. Found {len(response.get('Buckets', []))} buckets.")
        
        # --- 3. Create a Test Resource (Medium Risk) ---
        print(f"\n--- 3. Creating Test Bucket: {TEST_BUCKET_NAME} ---")
        logging.info(f"Attempting s3.create_bucket(). Expecting Medium Risk approval...")
        
        # Explicitly specify region to avoid AWS error
        s3_client.create_bucket(
            Bucket=TEST_BUCKET_NAME,
            CreateBucketConfiguration={'LocationConstraint': TEST_REGION}
        )
        logging.info(f"SUCCESS: Test bucket created in {TEST_REGION}.")

        # --- 4. Test CRITICAL Risk Action (Should be DENIED by Ascend API) ---
        print(f"\n--- 4. Testing CRITICAL Risk Action (s3:delete_bucket) ---")
        print("⚠️ EXPECTING A PermissionError / DENIAL from the Ascend API...")
        
        # This action should trigger the Ascend API, which should deny it based on policy.
        s3_client.delete_bucket(Bucket=TEST_BUCKET_NAME)
        
        # This line should NOT be reached if the denial works
        logging.error("FAILURE: Critical action was NOT denied. Check Ascend Policy configuration.")

    except PermissionError as e:
        # --- Test Success: Denial was correctly handled ---
        logging.warning("✅ Test Successful: CRITICAL action correctly DENIED by Ascend policy.")
        logging.warning(f"Denial Reason: {e}")
        
    except ClientError as e:
        logging.error(f"❌ AWS Client Error encountered: {e}")
        
    except Exception as e:
        logging.error(f"❌ An unexpected error occurred: {e}")
        
    finally:
        # --- 5. Cleanup and Disable ---
        print("\n--- 5. Cleanup and Disabling Governance Hook ---")
        
        # Clean up the resource outside the governance hook for guaranteed deletion
        try:
            # Re-initialize client without the wrapper hook active for cleanup
            raw_s3_client = boto3.client('s3', region_name=TEST_REGION)
            raw_s3_client.delete_bucket(Bucket=TEST_BUCKET_NAME)
            logging.info(f"Cleanup: Test bucket {TEST_BUCKET_NAME} deleted using raw Boto3 client.")
        except ClientError:
            # Ignore errors if the bucket never got created or was already deleted
            pass
        except Exception:
            pass
            
        disable_governance()
        print("\n==================================================")
        print("✅ Test Execution Complete.")
        print("==================================================")

if __name__ == "__main__":
    run_test()

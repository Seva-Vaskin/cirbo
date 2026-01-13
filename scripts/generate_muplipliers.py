import os
import argparse
import logging

from cirbo.synthesis.generation.arithmetics.multiplication import generate_mul, MulMode

# Configure logging
logging.basicConfig(
    level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def generate_and_save_multipliers(size: int, output_dir: str):
    """
    Generates multipliers for all modes and saves them as AIG circuits in BENCH format.

    The circuits are converted to AIG basis (INPUT, AND, NOT, ALWAYS_TRUE, ALWAYS_FALSE)
    using the into_aig() method, then saved in BENCH format.

    """
    # 1. Create directory if it doesn't exist
    if not os.path.exists(output_dir):
        try:
            os.makedirs(output_dir)
            logger.info(f"Created directory: {output_dir}")
        except OSError as e:
            logger.error(f"Error creating directory {output_dir}: {e}")
            return

    # 2. Iterate through all available multiplication modes
    for mode in MulMode:
        mode_name = mode.value
        # Save as .bench since that's the available format; circuit is in AIG basis
        filename = f"mul_{mode_name.lower()}_{size}.bench"
        file_path = os.path.join(output_dir, filename)

        logger.info(f"Attempting to generate {mode_name} multiplier for size {size}...")

        try:
            # 3. Generate the circuit
            # We generate an S x S multiplier (Input A size = S, Input B size = S)
            circuit = generate_mul(
                size_of_input_a=size,
                size_of_input_b=size,
                type=mode,
                big_endian=False,  # Standard logic convention usually LSB first
            )

            # 4. Convert to AIG basis (INPUT, AND, NOT only)
            circuit.into_aig()

            # 5. Save to file in BENCH format
            circuit.save_to_file(file_path)
            logger.info(
                f"Success: Saved {filename} "
                f"(gates: {circuit.size}, inputs: {circuit.input_size}, "
                f"outputs: {circuit.output_size})"
            )

        except Exception as e:
            # Catch errors for specific algorithms that might have constraints
            # (e.g., POW2_M1 might require size to be 2^k - 1)
            logger.error(f"Failed to generate {mode_name} for size {size}. Reason: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Generate AIG-basis multipliers for a specific input size."
    )

    parser.add_argument(
        "-s",
        "--size",
        type=int,
        required=True,
        help="The bit size of the inputs (S). Resulting multiplier will be S x S.",
    )

    parser.add_argument(
        "-d",
        "--dir",
        type=str,
        default="./aig_output",
        help="Directory to save the generated files. Defaults to './aig_output'.",
    )

    args = parser.parse_args()

    print(f"--- Starting Generation for Input Size: {args.size} ---")
    generate_and_save_multipliers(args.size, args.dir)
    print("--- Process Complete ---")


if __name__ == "__main__":
    main()
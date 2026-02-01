# -*- coding: utf-8 -*-
"""
Image Analysis Engine for CEN AI DAM Editor

This module provides AI-powered product image analysis:
- Category classification
- Attribute extraction (product-specific and common)
- Product description generation
- Metadata generation for DAM system
"""

import os
import json
from typing import List, Dict, Optional

from .gemini_client import GeminiClient
from .prompt_templates import PromptTemplates
from .config import PRODUCT_CATEGORY, PRODUCT_ATTRIBUTE, COMMON_ATTRIBUTE


class ImageAnalyzer:
    """
    AI-powered image analysis engine.

    Analyzes product images to extract:
    - Product category and sub-category
    - Category-specific attributes
    - Common attributes (style, color, pattern, target)
    - Marketing description
    """

    def __init__(self, output_dir: str):
        """
        Initialize ImageAnalyzer.

        Args:
            output_dir: Directory to save analysis results (JSON metadata)
        """
        self.output_dir = output_dir
        self.gemini = GeminiClient()
        os.makedirs(self.output_dir, exist_ok=True)

    def analyze_image(
        self,
        image_path: str,
        brand: str = "Furniture",
        save_metadata: bool = True
    ) -> Dict:
        """
        Perform complete analysis of a product image.

        Args:
            image_path: Path to image file
            brand: Brand category ("Samsung Electronics", "Furniture", "Cosmetics")
            save_metadata: Whether to save metadata JSON file

        Returns:
            Dictionary containing all analysis results
        """
        print(f"\n{'='*60}")
        print(f"Analyzing: {os.path.basename(image_path)}")
        print(f"{'='*60}")

        try:
            # Step 1: Category Classification
            print("Step 1/4: Classifying product category...")
            category_data = self._analyze_category(image_path, brand)
            main_category = category_data.get('category', '')
            sub_category = category_data.get('sub_category', '')
            print(f"  ✓ Category: {main_category} > {sub_category}")

            # Step 2: Product-Specific Attributes
            print("Step 2/4: Extracting product-specific attributes...")
            product_attributes = self._analyze_product_attributes(
                image_path, brand, main_category
            )
            print(f"  ✓ Found {len(product_attributes)} product attributes")

            # Step 3: Common Attributes
            print("Step 3/4: Extracting common attributes...")
            common_attributes = self._analyze_common_attributes(image_path)
            print(f"  ✓ Found {len(common_attributes)} common attributes")

            # Step 4: Generate Description
            print("Step 4/4: Generating product description...")
            all_attributes = {**product_attributes, **common_attributes}
            description = self._generate_description(
                main_category, sub_category, all_attributes
            )
            print(f"  ✓ Description generated")

            # Compile result
            result = {
                'image_path': image_path,
                'filename': os.path.basename(image_path),
                'brand': brand,
                'category': main_category,
                'sub_category': sub_category,
                'category_data': category_data,
                'product_attributes': product_attributes,
                'common_attributes': common_attributes,
                'all_attributes': all_attributes,
                'description': description
            }

            # Save metadata
            if save_metadata:
                self._save_metadata(result)

            print(f"{'='*60}")
            print(f"✓ Analysis complete!")
            print(f"{'='*60}\n")

            return result

        except Exception as e:
            print(f"✗ Error analyzing {image_path}: {e}")
            raise

    def analyze_batch(
        self,
        image_paths: List[str],
        brand: str = "Furniture"
    ) -> List[Dict]:
        """
        Analyze multiple images in batch.

        Args:
            image_paths: List of image file paths
            brand: Brand category

        Returns:
            List of analysis result dictionaries
        """
        results = []
        total = len(image_paths)

        print(f"\n🔍 Starting batch analysis ({total} images)...\n")

        for idx, image_path in enumerate(image_paths, 1):
            print(f"[{idx}/{total}] {os.path.basename(image_path)}")
            try:
                result = self.analyze_image(image_path, brand=brand)
                results.append(result)
            except Exception as e:
                print(f"  ✗ Skipping due to error: {e}\n")
                continue

        print(f"\n✓ Batch analysis complete: {len(results)}/{total} succeeded\n")
        return results

    # ================================================================
    # PRIVATE ANALYSIS METHODS
    # ================================================================

    def _analyze_category(self, image_path: str, brand: str) -> Dict:
        """Classify product category and sub-category."""
        brand_categories = PRODUCT_CATEGORY.get(brand, {})

        prompt_text = PromptTemplates.product_category_analysis(
            product_categories=json.dumps(brand_categories, ensure_ascii=False, indent=2)
        )

        response = self.gemini.analyze_image(
            prompt=prompt_text,
            image_path=image_path
        )

        return json.loads(response)

    def _analyze_product_attributes(
        self,
        image_path: str,
        brand: str,
        category: str
    ) -> Dict:
        """Extract product-specific attributes based on category."""
        brand_attributes = PRODUCT_ATTRIBUTE.get(brand, {})

        if category not in brand_attributes:
            print(f"  ⚠ No specific attributes defined for {category}")
            return {}

        attributes_config = brand_attributes[category]

        prompt_text = PromptTemplates.product_attribute_analysis(
            category=category,
            attributes_config=json.dumps(attributes_config, ensure_ascii=False, indent=2)
        )

        response = self.gemini.analyze_image(
            prompt=prompt_text,
            image_path=image_path
        )

        return json.loads(response)

    def _analyze_common_attributes(self, image_path: str) -> Dict:
        """Extract common attributes (style, color, pattern, target)."""
        prompt_text = PromptTemplates.common_attribute_analysis(
            colors=COMMON_ATTRIBUTE['색상'],
            patterns=COMMON_ATTRIBUTE['무늬'],
            styles=COMMON_ATTRIBUTE['스타일'],
            target_customers=COMMON_ATTRIBUTE['타겟 고객'],
            target_ages=COMMON_ATTRIBUTE['타겟 연령층']
        )

        response = self.gemini.analyze_image(
            prompt=prompt_text,
            image_path=image_path
        )

        return json.loads(response)

    def _generate_description(
        self,
        category: str,
        sub_category: str,
        attributes: Dict
    ) -> str:
        """Generate marketing description from attributes."""
        prompt_text = PromptTemplates.product_description(attributes=attributes)

        response = self.gemini.generate_text(
            prompt=prompt_text,
            response_type="application/json"
        )

        description_data = json.loads(response)
        return description_data.get("description", "")

    def _save_metadata(self, result: Dict) -> str:
        """Save analysis result as JSON metadata file."""
        filename = result['filename']
        base = os.path.splitext(filename)[0]
        metadata_path = os.path.join(self.output_dir, f"{base}.json")

        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        print(f"  💾 Metadata saved: {metadata_path}")
        return metadata_path
# -*- coding: utf-8 -*-
"""
Image Generation Engine for CEN AI DAM Editor

This module provides high-level image generation functions using Gemini API.
Supports various templates: SNS/Marketing, Detail Page, Studio Shooting, etc.
"""

import os
import json
from datetime import datetime
from typing import List, Dict, Optional, Tuple

from .gemini_client import GeminiClient
from .prompt_templates import PromptTemplates


class ImageGenerator:
    """
    AI-powered image generation engine.

    Supports multiple generation modes:
    - Basic transformations (change attributes, apply style, replace objects)
    - Template-based generation (SNS/Marketing, Detail Page, Studio Shooting)
    - Advanced features (Multilingual conversion, Infographics)
    """

    def __init__(self, output_dir: str):
        """
        Initialize ImageGenerator.

        Args:
            output_dir: Directory to save generated images
        """
        self.output_dir = output_dir
        self.gemini = GeminiClient()
        os.makedirs(self.output_dir, exist_ok=True)

    # ================================================================
    # BASIC GENERATION METHODS
    # ================================================================

    def change_attributes(
        self,
        image_path: str,
        instructions: List[str]
    ) -> List[str]:
        """
        Change specific attributes (color, angle, etc.) of an image.

        Args:
            image_path: Path to source image
            instructions: List of change instructions

        Returns:
            List of paths to saved generated images
        """
        prompt_text = PromptTemplates.change_attributes(", ".join(instructions))
        generated_image_data, _ = self.gemini.generate_image(
            prompt=prompt_text,
            reference_images=[image_path]
        )

        output_path = self._get_output_path(image_path, "_changed")
        return self._save_images(generated_image_data, output_path)

    def create_thumbnail_with_metadata(
        self,
        image_path: str,
        metadata_path: str
    ) -> List[str]:
        """
        Generate thumbnail with metadata overlay.

        Args:
            image_path: Path to product image
            metadata_path: Path to JSON metadata file

        Returns:
            List of paths to saved thumbnail images
        """
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)

        description = metadata.get("description", "")
        if isinstance(description, dict):
            description = description.get("description", "")

        prompt_text = PromptTemplates.create_thumbnail_with_metadata(metadata=description)
        generated_image_data, _ = self.gemini.generate_image(
            prompt=prompt_text,
            reference_images=[image_path]
        )

        output_path = self._get_output_path(image_path, "_thumbnail_meta")
        return self._save_images(generated_image_data, output_path)

    def apply_style_from_reference(
        self,
        product_image_path: str,
        reference_image_paths: List[str]
    ) -> List[str]:
        """
        Apply style from reference images to product image.

        Args:
            product_image_path: Path to product image
            reference_image_paths: Paths to reference style images

        Returns:
            List of paths to saved styled images
        """
        prompt_text = PromptTemplates.apply_style_from_reference()
        all_images = [product_image_path] + reference_image_paths

        generated_image_data, _ = self.gemini.generate_image(
            prompt=prompt_text,
            reference_images=all_images
        )

        output_path = self._get_output_path(product_image_path, "_styled")
        return self._save_images(generated_image_data, output_path)

    def replace_object_in_reference(
        self,
        product_image_path: str,
        reference_image_paths: List[str]
    ) -> List[str]:
        """
        Replace/composite product into reference scene.

        Args:
            product_image_path: Path to product image
            reference_image_paths: Paths to reference scene images

        Returns:
            List of paths to saved composite images
        """
        prompt_text = PromptTemplates.replace_object_in_reference(
            object_to_replace=product_image_path
        )
        all_images = [product_image_path] + reference_image_paths

        generated_image_data, _ = self.gemini.generate_image(
            prompt=prompt_text,
            reference_images=all_images
        )

        output_path = self._get_output_path(product_image_path, "_replaced")
        return self._save_images(generated_image_data, output_path)

    def create_interior_scene(
        self,
        product_image_paths: List[str]
    ) -> List[str]:
        """
        Combine multiple products into harmonious interior scene.

        Args:
            product_image_paths: Paths to product images

        Returns:
            List of paths to saved scene images
        """
        prompt_text = PromptTemplates.create_interior_scene()
        generated_image_data, _ = self.gemini.generate_image(
            prompt=prompt_text,
            reference_images=product_image_paths
        )

        output_path = os.path.join(self.output_dir, "interior_scene.png")
        return self._save_images(generated_image_data, output_path)

    # ================================================================
    # TEMPLATE-BASED GENERATION METHODS
    # ================================================================

    def generate_sns_marketing(
        self,
        product_name: str,
        product_images: List[str],
        target_audience: str,
        layout: str,
        concept: str,
        copy: Optional[Dict[str, str]] = None
    ) -> List[str]:
        """
        Generate SNS/Marketing material using template.

        Args:
            product_name: Name of the product
            product_images: Paths to product images
            target_audience: Target customer description
            layout: Layout specification (e.g., "1:1 정방형")
            concept: Marketing concept/purpose
            copy: Dictionary with 'main', 'sub', 'hashtags' keys

        Returns:
            List of paths to generated marketing images
        """
        prompt_text = PromptTemplates.sns_marketing_template(
            product_name=product_name,
            target_audience=target_audience,
            layout=layout,
            concept=concept,
            copy=copy
        )

        generated_image_data, _ = self.gemini.generate_image(
            prompt=prompt_text,
            reference_images=product_images
        )

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(self.output_dir, f"sns_marketing_{timestamp}.png")
        return self._save_images(generated_image_data, output_path)

    def generate_detail_page(
        self,
        product_name: str,
        product_images: List[str],
        layout_ratio: str,
        reference_frame: Optional[str] = None
    ) -> List[str]:
        """
        Generate product detail page / catalog.

        Args:
            product_name: Product name
            product_images: Paths to product images
            layout_ratio: Aspect ratio (e.g., "9:16")
            reference_frame: Optional reference layout frame

        Returns:
            List of paths to generated detail page images
        """
        prompt_text = PromptTemplates.detail_page_template(
            product_name=product_name,
            product_images=product_images,
            layout_ratio=layout_ratio,
            reference_frame=reference_frame
        )

        generated_image_data, _ = self.gemini.generate_image(
            prompt=prompt_text,
            reference_images=product_images
        )

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(self.output_dir, f"detail_page_{timestamp}.png")
        return self._save_images(generated_image_data, output_path)

    def generate_studio_shooting(
        self,
        product_image: str,
        model_setting: Optional[str] = None,
        combination_products: Optional[List[str]] = None,
        shooting_concept: str = "미니멀리즘 하이엔드 패션 룩북"
    ) -> List[str]:
        """
        Generate studio shooting images (model fitting, background).

        Args:
            product_image: Path to main product image
            model_setting: Model configuration
            combination_products: Optional additional product images for cross-sell
            shooting_concept: Shooting concept description

        Returns:
            List of paths to generated studio images
        """
        all_images = [product_image]
        if combination_products:
            all_images.extend(combination_products)

        prompt_text = PromptTemplates.studio_shooting_template(
            product_image=product_image,
            model_setting=model_setting,
            combination_products=combination_products,
            shooting_concept=shooting_concept
        )

        generated_image_data, _ = self.gemini.generate_image(
            prompt=prompt_text,
            reference_images=all_images
        )

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(self.output_dir, f"studio_shot_{timestamp}.png")
        return self._save_images(generated_image_data, output_path)

    # ================================================================
    # HELPER METHODS
    # ================================================================

    def _get_output_path(self, original_path: str, suffix: str) -> str:
        """Generate output file path with suffix."""
        base, ext = os.path.splitext(os.path.basename(original_path))
        return os.path.join(self.output_dir, f"{base}{suffix}{ext}")

    def _save_images(self, image_data: List, output_path: str) -> List[str]:
        """
        Save generated image data to files.

        Args:
            image_data: List of image data from Gemini API
            output_path: Base output path

        Returns:
            List of saved file paths
        """
        saved_files = []

        if not image_data:
            print("Warning: No images generated")
            return saved_files

        # Handle multiple images
        if len(image_data) > 1:
            base, ext = os.path.splitext(output_path)
            for idx, data in enumerate(image_data):
                indexed_path = f"{base}_{idx + 1}{ext}"
                with open(indexed_path, 'wb') as f:
                    f.write(data.data)
                print(f"✓ Image saved: {indexed_path}")
                saved_files.append(indexed_path)
        else:
            # Single image
            with open(output_path, 'wb') as f:
                f.write(image_data[0].data)
            print(f"✓ Image saved: {output_path}")
            saved_files.append(output_path)

        return saved_files

    def generate_style_based_image(
        self,
        product_image: str,
        reference_images: List[str],
        placement: str,
        environment: str,
        mood: List[str],
        lighting: str = "자연광"
    ) -> List[str]:
        """
        Generate style-based image with product placement.

        Args:
            product_image: Path to product image
            reference_images: Paths to reference style images
            placement: Placement requirements
            environment: Environment/scene setting
            mood: List of mood descriptors
            lighting: Lighting type

        Returns:
            List of paths to generated images
        """
        mood_text = ", ".join(mood) if mood else "자연스러운"

        prompt_text = f"""
Product Placement & Style-based Image Generation

Create a realistic lifestyle image featuring the product in the specified environment.

**Product**: Use the uploaded product image
**Environment**: {environment}
**Placement**: {placement}
**Style Reference**: Apply the visual style, composition, and atmosphere from the reference images
**Mood**: {mood_text}
**Lighting**: {lighting}

Requirements:
1. Place the product naturally in the environment
2. Match the style, color palette, and atmosphere of reference images
3. Ensure realistic lighting and shadows
4. Maintain product visibility and focus
5. Create a cohesive, magazine-quality composition

Generate a high-quality lifestyle image that showcases the product in an appealing context.
"""

        # Combine product and reference images
        all_images = [product_image] + reference_images

        generated_image_data, _ = self.gemini.generate_image(
            prompt=prompt_text,
            reference_images=all_images
        )

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(self.output_dir, f"style_based_{timestamp}.png")
        return self._save_images(generated_image_data, output_path)

    def generate_illustration(
        self,
        content_type: str,
        text_content: str,
        subject: str,
        visual_style: str,
        color_palette: str,
        composition: str = "자동",
        aspect_ratio: str = "16:9 와이드",
        mood: str = "",
        details: str = ""
    ) -> List[str]:
        """
        Generate illustration image based on text content.

        Args:
            content_type: Type of content (news, web novel, etc.)
            text_content: Text to illustrate
            subject: Main subject/theme
            visual_style: Visual style (realistic, watercolor, etc.)
            color_palette: Color palette description
            composition: Composition style
            aspect_ratio: Image aspect ratio
            mood: Mood/atmosphere
            details: Additional details

        Returns:
            List of paths to generated images
        """
        prompt_text = f"""
Illustration Image Generation for {content_type}

Create an illustration that visually represents the following text content:

**Text Content**:
{text_content}

**Main Subject/Theme**: {subject}
**Visual Style**: {visual_style}
**Color Palette**: {color_palette}
**Composition**: {composition}
**Aspect Ratio**: {aspect_ratio}
**Mood/Atmosphere**: {mood if mood else "자연스럽고 몰입감 있는"}
**Additional Details**: {details if details else "없음"}

Requirements:
1. Capture the essence and key elements of the text
2. Create a compelling visual narrative
3. Use the specified visual style consistently
4. Apply appropriate color palette and composition
5. Ensure the illustration complements and enhances the text content

Generate a professional-quality illustration suitable for {content_type}.
"""

        generated_image_data, _ = self.gemini.generate_image(
            prompt=prompt_text,
            reference_images=[]
        )

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(self.output_dir, f"illustration_{timestamp}.png")
        return self._save_images(generated_image_data, output_path)

    def complete_artwork(
        self,
        sketch_image: str,
        artwork_type: str,
        coloring_style: str,
        color_scheme: Dict,
        detail_level: str,
        shading: bool = True,
        light_source: str = "자동",
        texture: List[str] = None,
        effects: Dict = None,
        instructions: str = ""
    ) -> List[str]:
        """
        Complete and colorize sketch/rough artwork.

        Args:
            sketch_image: Path to sketch image
            artwork_type: Type of artwork (character, fashion design, etc.)
            coloring_style: Coloring style
            color_scheme: Color scheme configuration
            detail_level: Level of detail
            shading: Whether to add shading
            light_source: Light source position
            texture: List of textures to add
            effects: Special effects configuration
            instructions: Additional instructions

        Returns:
            List of paths to completed images
        """
        # Build color instructions
        color_instruction = ""
        if color_scheme['method'] == 'palette':
            color_instruction = f"Use the following color palette: Primary {color_scheme.get('primary', '')}, Secondary {color_scheme.get('secondary', '')}, Accent {color_scheme.get('accent', '')}"
        elif color_scheme['method'] == 'reference':
            color_instruction = "Extract and apply colors from the reference image"
        else:
            color_instruction = "Use AI-recommended harmonious color palette"

        # Build texture instruction
        texture_list = texture if texture and texture != ["없음"] else []
        texture_instruction = f"Add textures: {', '.join(texture_list)}" if texture_list else "No additional texture"

        # Build effects instruction
        effects_list = []
        if effects:
            if effects.get('glow'): effects_list.append("glow effect")
            if effects.get('blur'): effects_list.append("background blur")
            if effects.get('grain'): effects_list.append("film grain")
        effects_instruction = f"Apply effects: {', '.join(effects_list)}" if effects_list else "No special effects"

        prompt_text = f"""
Artwork Completion and Coloring

Transform the uploaded sketch into a fully completed, professionally colored illustration.

**Artwork Type**: {artwork_type}
**Coloring Style**: {coloring_style}
**Detail Level**: {detail_level}
**Color Scheme**: {color_instruction}
**Shading**: {"Add realistic shading with light source from " + light_source if shading else "Flat coloring without shading"}
**Texture**: {texture_instruction}
**Effects**: {effects_instruction}
**Additional Instructions**: {instructions if instructions else "없음"}

Requirements:
1. Preserve the original sketch's composition and line work
2. Apply professional-quality coloring
3. Add appropriate depth and dimension
4. Ensure color harmony and visual appeal
5. Maintain the artistic intent of the original sketch
6. Apply the specified detail level consistently

Complete the artwork with the highest quality, ready for final use.
"""

        # Add reference color image if provided
        reference_images = [sketch_image]
        if color_scheme['method'] == 'reference' and color_scheme.get('reference_image'):
            reference_images.append(color_scheme['reference_image'])

        generated_image_data, _ = self.gemini.generate_image(
            prompt=prompt_text,
            reference_images=reference_images
        )

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(self.output_dir, f"artwork_complete_{timestamp}.png")
        return self._save_images(generated_image_data, output_path)

    def generate_multilingual_image(
        self,
        original_image: str,
        target_language: str,
        font_family: str = "",
        emphasis_keywords: str = "",
        translation_tone: str = "일반",
        requirements: str = ""
    ) -> List[str]:
        """
        Generate multilingual version of image with translated text.

        Args:
            original_image: Path to original image with text
            target_language: Target language for translation
            font_family: Font family to use (optional)
            emphasis_keywords: Keywords to emphasize (optional)
            translation_tone: Tone of translation
            requirements: Additional requirements

        Returns:
            List of paths to generated images
        """
        prompt_text = f"""
Multilingual Image Conversion

Create a new version of this image with all text translated to {target_language}.

**Original Image**: Contains text that needs translation
**Target Language**: {target_language}
**Font Settings**: {font_family if font_family else "Auto-select appropriate font for target language"}
**Emphasis Keywords**: {emphasis_keywords if emphasis_keywords else "None"}
**Translation Tone**: {translation_tone}
**Additional Requirements**: {requirements if requirements else "None"}

Requirements:
1. Translate all visible text in the image to {target_language}
2. Maintain the original layout and design
3. Use culturally appropriate fonts and typography
4. Preserve image quality and visual hierarchy
5. Ensure translations are contextually accurate
6. Apply appropriate text formatting for the target language
7. Maintain brand consistency and visual appeal

Generate a professional-quality multilingual version suitable for {target_language} markets.
"""

        generated_image_data, _ = self.gemini.generate_image(
            prompt=prompt_text,
            reference_images=[original_image]
        )

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(self.output_dir, f"multilingual_{target_language}_{timestamp}.png")
        return self._save_images(generated_image_data, output_path)

    def generate_infographic(
        self,
        data_source_description: str,
        content_type: str,
        purpose: str,
        target_audience: str = "",
        visual_style: str = "프레젠테이션 슬라이드",
        key_message: str = ""
    ) -> List[str]:
        """
        Generate infographic image from data.

        Args:
            data_source_description: Description of the data to visualize
            content_type: Type of content (시리즈형 or 단일형)
            purpose: Purpose of the infographic
            target_audience: Target audience
            visual_style: Visual style
            key_message: Key message to convey

        Returns:
            List of paths to generated images
        """
        prompt_text = f"""
Infographic Image Generation

Create a professional infographic that visualizes the following information:

**Data/Content**:
{data_source_description}

**Content Type**: {content_type}
**Purpose**: {purpose}
**Target Audience**: {target_audience if target_audience else "General audience"}
**Visual Style**: {visual_style}
**Key Message**: {key_message if key_message else "Clearly communicate the data"}

Requirements:
1. Create a visually compelling infographic design
2. Use appropriate charts, graphs, icons, and visual elements
3. Ensure information hierarchy and flow
4. Apply consistent color scheme and typography
5. Make data easy to understand at a glance
6. Include clear labels and legends
7. Optimize for readability and engagement
8. Match the specified visual style: {visual_style}

Visual Style Guidelines:
- 프레젠테이션 슬라이드: Clean, professional, suitable for presentations
- 그리드형: Organized grid layout with clear sections
- 타임라인: Chronological flow with timeline visualization
- 플로우차트: Process flow with connected steps
- 인포그래픽 차트: Data-driven charts and visualizations

Generate a high-quality infographic optimized for {purpose}.
"""

        generated_image_data, _ = self.gemini.generate_image(
            prompt=prompt_text,
            reference_images=[]
        )

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(self.output_dir, f"infographic_{timestamp}.png")
        return self._save_images(generated_image_data, output_path)
.PHONY: install run test clean flatpak-build flatpak-install

# Install Python dependencies
install:
	pip3 install --user -e ".[dev]"

# Run the app
run:
	PYTHONPATH=src python3 -m doubao_murmur

# Run tests
test:
	PYTHONPATH=src python3 -m pytest tests/ -v

# Build Flatpak
flatpak-build:
	flatpak-builder --force-clean build-dir flatpak/com.doubao.Murmur.yml
	flatpak-builder --repo=repo --force-clean build-dir flatpak/com.doubao.Murmur.yml

# Install Flatpak locally
flatpak-install: flatpak-build
	flatpak --user remote-add --if-not-exists doubao-murmur repo --no-gpg-verify
	flatpak --user install -y doubao-murmur com.doubao.Murmur

# Clean build artifacts
clean:
	rm -rf build-dir repo .flatpak-builder
	rm -rf src/*.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

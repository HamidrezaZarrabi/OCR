# remove annotation of each file
sudo apt install pdftk

for pdf in *.PDF
do
	pdftk "$pdf" output uncompressed.pdf uncompress

	LANG=C sed -n '/^\/Annots/!p' uncompressed.pdf > stripped.pdf

	pdftk stripped.pdf output "$pdf" compress

	rm uncompressed.pdf

	rm stripped.pdf
done

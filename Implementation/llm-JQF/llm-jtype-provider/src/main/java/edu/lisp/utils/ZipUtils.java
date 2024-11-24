package edu.lisp.utils;

import org.apache.commons.compress.archivers.zip.ZipArchiveEntry;
import org.apache.commons.compress.archivers.zip.ZipFile;

import java.io.*;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.Enumeration;
import java.util.List;
import java.util.Optional;

public class ZipUtils {
    private static final String UNZIP_TEMPORARY_DIR = System.getProperty("user.dir") + File.separator + ".unzip";

    /**
     * Exposed API
     * Used to unzip a list of src jar paths
     * @param srcJarPaths a list of paths to *-source.jar
     * @return a list of the roots of package
     */
    public static List<String> unzipSourceJars(List<String> srcJarPaths) {
        List<String> results = new ArrayList<>();
        for (String srcJarPath : srcJarPaths) {
            Optional<String> oExtractDir = Optional.empty();
            try { oExtractDir = unzipSourceJar(srcJarPath); }
            catch (IOException ignored) { continue; }
            oExtractDir.ifPresent(results::add);
        }
        return results;
    }

    /**
     * @throws IOException
     */
    public static Optional<String> unzipSourceJar(String srcJarPath) throws IOException {
        Optional<String> oSrcJarFileName = FileUtils.getFileName(srcJarPath);
        if (oSrcJarFileName.isEmpty()) {
            throw new IOException(
                    "unzipSourceJar cannot get the name of file: " + srcJarPath);
        }

        Path extractPath = Paths.get(ZipUtils.UNZIP_TEMPORARY_DIR, oSrcJarFileName.get());
        String extractPathStr = extractPath.toAbsolutePath().toString();
        File extractPathDir = new File(extractPathStr);
        if (!extractPathDir.exists()) {
            if (!extractPathDir.mkdirs()) {
                throw new IOException(
                        "unzipSourceJar cannot mkdir for " + extractPathStr);
            }
        } else {
            if (extractPathDir.delete()) {
                throw new IOException(
                        "unzipSourceJar requires " + extractPathStr + " to be empty." +
                        "Now it's a file and it cannot be deleted");
            }
        }

        try {
            unzipUTF8(srcJarPath, extractPathStr);
        } catch (FileNotFoundException e) {
            return Optional.empty();
        } catch (IOException e) {
            e.printStackTrace();
            return Optional.empty();
        }
        return Optional.of(extractPathStr);
    }

    /**
     * unzip
     * 将 zipPath 这个 zip 文件以 encoding 解压到 extractDir 对应的目录下
     * @param zipPath zip 文件的相对 / 绝对路径
     * @param extractDir zip 文件解压后的内部文件存放的路径
     * @param encoding 解压缩使用的编码格式
     * @throws FileNotFoundException
     * @throws IOException
     */
    public static void unzip(String zipPath, String extractDir, String encoding)
            throws FileNotFoundException, IOException {
        File zipFile = new File(zipPath);
        if (!zipFile.exists()) {
            throw new FileNotFoundException(String.format("%s not existed.", zipPath));
        }

        File extractFolder = new File(extractDir);
        if (!extractFolder.exists()) {
            extractFolder.mkdirs();
        }

        try (ZipFile tmp = new ZipFile(zipPath, encoding)) {
            Enumeration<ZipArchiveEntry> entries = tmp.getEntries(); // 获取 jar 中各个文件的 entry
            while (entries.hasMoreElements()) {
                ZipArchiveEntry entry = entries.nextElement();
                String singleFileNameInZipFile = entry.getName();
                String singleFilePathInFS = extractDir + File.separator + singleFileNameInZipFile;
                if (entry.isDirectory()) {
                    // entry 是 dir 则递归创建 dir
                    File dir = new File(singleFilePathInFS);
                    if (!dir.exists()) {
                        dir.mkdirs();
                    }
                } else {
                    // entry 是 file 则使用 bis / bos 将文件拷出
                    Optional<File> singleFileInFSOpt = FileUtils.getFileAfterCreateFolder(singleFilePathInFS);
                    if (!singleFileInFSOpt.isPresent()) {
                        throw new IOException(String.format("%s not existed", singleFilePathInFS));
                    }
                    File singleFileInFS = singleFileInFSOpt.get();

                    try (
                            InputStream is = tmp.getInputStream(entry);
                            BufferedInputStream bis = new BufferedInputStream(is);
                            FileOutputStream fos = new FileOutputStream(singleFileInFS);
                            BufferedOutputStream bos = new BufferedOutputStream(fos);
                    ) {
                        int len;
                        byte[] buffer = new byte[5120];
                        while ((len = bis.read(buffer)) != -1) {
                            bos.write(buffer, 0, len);
                        }
                    } catch (IOException e) {
                        e.printStackTrace();
                        throw new IOException(String.format("%s -> %s, failed to write file", singleFileNameInZipFile, singleFilePathInFS), e);
                    }
                }
            }
        } catch (IOException e) {
            throw new IOException(String.format("failed to unzip file %s", zipPath), e);
        }
    }

    /**
     * unzipGBK
     *
     * 将 zipPath 这个 zip 文件以 encoding 解压到 extractDir 对应的目录下
     * @param zipPath zip 文件的相对 / 绝对路径
     * @param extractDir zip 文件解压后的内部文件存放的路径
     * @throws FileNotFoundException
     * @throws IOException
     */
    public static void unzipGBK(String zipPath, String extractDir)
            throws FileNotFoundException, IOException {
        ZipUtils.unzip(zipPath, extractDir, "gbk");
    }

    /**
     * unzipUTF8
     *
     * 将 zipPath 这个 zip 文件以 encoding 解压到 extractDir 对应的目录下
     * @param zipPath zip 文件的相对 / 绝对路径
     * @param extractDir zip 文件解压后的内部文件存放的路径
     * @throws FileNotFoundException
     * @throws IOException
     */
    public static void unzipUTF8(String zipPath, String extractDir)
            throws FileNotFoundException, IOException {
        ZipUtils.unzip(zipPath, extractDir, "UTF-8");
    }
}